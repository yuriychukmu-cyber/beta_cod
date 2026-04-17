from __future__ import annotations

import logging
import os
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Tuple

from datssol.adapters.api_client import ApiClient
from datssol.bots.heuristic_bot import HeuristicBot

try:
    from datssol.bots.neural_bot import NeuralBot
except Exception:
    NeuralBot = None


Coord = Tuple[int, int]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


class SlidingWindowRateLimiter:
    """
    Не более max_requests за period_seconds в скользящем окне.
    Для этой игры держим не больше 2 запросов в 1 секунду.
    """

    def __init__(self, max_requests: int = 2, period_seconds: float = 1.0) -> None:
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self.request_times: Deque[float] = deque()

    def wait_for_slot(self) -> None:
        while True:
            now = time.monotonic()

            while self.request_times and now - self.request_times[0] >= self.period_seconds:
                self.request_times.popleft()

            if len(self.request_times) < self.max_requests:
                self.request_times.append(now)
                return

            sleep_for = self.period_seconds - (now - self.request_times[0]) + 0.01
            time.sleep(max(0.02, sleep_for))


def build_bot():
    mode = os.environ.get("DATSSOL_MODE", "heuristic").lower()
    checkpoint = os.environ.get("DATSSOL_CHECKPOINT", "")

    if mode == "neural":
        if NeuralBot is None:
            raise RuntimeError("NeuralBot не импортируется")
        if not checkpoint:
            raise RuntimeError("Для DATSSOL_MODE=neural нужна DATSSOL_CHECKPOINT")
        logging.info("Запуск NeuralBot, checkpoint=%s", checkpoint)
        return NeuralBot(checkpoint_path=checkpoint)

    logging.info("Запуск HeuristicBot")
    return HeuristicBot()


def is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "http 429" in text or "too many requests" in text or '"errcode":24' in text


def response_has_duplicate_submit(response: Any) -> bool:
    if not isinstance(response, dict):
        return False
    errors = response.get("errors", []) or []
    return any("command already submitted this turn" in str(err).lower() for err in errors)


def response_has_invalid_command(response: Any) -> bool:
    if not isinstance(response, dict):
        return False
    errors = response.get("errors", []) or []
    lowered = [str(e).lower() for e in errors]
    return any("invalid command" in e for e in lowered) or any("no valid actions remain" in e for e in lowered)


def to_coord(v: List[int]) -> Coord:
    return int(v[0]), int(v[1])


def format_coord(c: Coord) -> str:
    return f"({c[0]},{c[1]})"


def in_square_range(a: Coord, b: Coord, radius: int) -> bool:
    return abs(a[0] - b[0]) <= radius and abs(a[1] - b[1]) <= radius


def compute_signal_range(arena: Dict[str, Any]) -> int:
    upgrades = arena.get("plantationUpgrades", {}) or {}
    tiers = upgrades.get("tiers", []) or []
    signal_level = 0
    for t in tiers:
        if t.get("name") == "signal_range":
            signal_level = int(t.get("current", 0))
            break
    return 3 + signal_level


def classify_action(arena: Dict[str, Any], target: Coord) -> str:
    own_positions = {to_coord(p["position"]) for p in (arena.get("plantations", []) or [])}
    enemy_positions = {to_coord(e["position"]) for e in (arena.get("enemy", []) or [])}
    beaver_positions = {to_coord(b["position"]) for b in (arena.get("beavers", []) or [])}
    construction_positions = {to_coord(c["position"]) for c in (arena.get("construction", []) or [])}

    if target in own_positions:
        return "REPAIR"
    if target in enemy_positions:
        return "SABOTAGE"
    if target in beaver_positions:
        return "BEAVER"
    if target in construction_positions:
        return "BUILD+"
    return "BUILD"


def format_single_action(arena: Dict[str, Any], cmd: Dict[str, Any]) -> str:
    path = cmd.get("path", [])
    if not isinstance(path, list) or len(path) != 3:
        return "INVALID_ACTION"

    author = to_coord(path[0])
    exit_pos = to_coord(path[1])
    target = to_coord(path[2])

    kind = classify_action(arena, target)
    via = "" if author == exit_pos else f" via {format_coord(exit_pos)}"
    return f"{kind:<8} {format_coord(author)}{via} -> {format_coord(target)}"


def format_payload_pretty(arena: Dict[str, Any], payload: Dict[str, Any]) -> str:
    parts: List[str] = []

    upgrade = payload.get("plantationUpgrade")
    if upgrade:
        parts.append(f"UPGRADE  {upgrade}")

    relocate = payload.get("relocateMain")
    if isinstance(relocate, list) and len(relocate) == 2:
        try:
            a = to_coord(relocate[0])
            b = to_coord(relocate[1])
            parts.append(f"RELOCATE {format_coord(a)} -> {format_coord(b)}")
        except Exception:
            parts.append("RELOCATE invalid")

    commands = payload.get("command", []) or []
    for cmd in commands:
        parts.append(format_single_action(arena, cmd))

    if not parts:
        return "NO_ACTIONS"

    return "\n    ".join(parts)


def format_response_pretty(response: Any) -> str:
    if not isinstance(response, dict):
        return str(response)

    code = response.get("code")
    errors = response.get("errors", []) or []

    if errors:
        return f"code={code} errors={errors}"
    return f"code={code} ok"


def sanitize_payload(payload: Dict[str, Any], arena: Dict[str, Any]) -> Dict[str, Any]:
    """
    Локально выбрасывает явно невалидные действия до отправки на сервер.
    """
    clean: Dict[str, Any] = {}

    own = [p for p in arena.get("plantations", []) or []]
    own_positions = {to_coord(p["position"]) for p in own}
    controllable_positions = {to_coord(p["position"]) for p in own if not p.get("isIsolated", False)}

    enemy_positions = {to_coord(e["position"]) for e in (arena.get("enemy", []) or [])}
    beaver_positions = {to_coord(b["position"]) for b in (arena.get("beavers", []) or [])}
    mountains = {to_coord(m) for m in (arena.get("mountains", []) or [])}

    action_range = int(arena.get("actionRange", 2))
    signal_range = compute_signal_range(arena)
    upgrades = arena.get("plantationUpgrades", {}) or {}
    upgrade_points = int(upgrades.get("points", 0))

    # plantationUpgrade
    upgrade_name = payload.get("plantationUpgrade")
    if isinstance(upgrade_name, str) and upgrade_name.strip():
        if upgrade_points > 0:
            tiers = {t["name"]: t for t in (upgrades.get("tiers", []) or []) if "name" in t}
            tier = tiers.get(upgrade_name)
            if tier and int(tier.get("current", 0)) < int(tier.get("max", 0)):
                clean["plantationUpgrade"] = upgrade_name

    # command
    clean_commands = []
    for cmd in payload.get("command", []) or []:
        path = cmd.get("path")
        if not isinstance(path, list) or len(path) != 3:
            continue

        try:
            author = to_coord(path[0])
            exit_pos = to_coord(path[1])
            target = to_coord(path[2])
        except Exception:
            continue

        if author not in controllable_positions:
            continue
        if exit_pos not in controllable_positions:
            continue
        if not in_square_range(author, exit_pos, signal_range):
            continue
        if not in_square_range(exit_pos, target, action_range):
            continue
        if target in mountains:
            continue

        # repair
        if target in own_positions:
            if target == author:
                continue
            clean_commands.append(
                {"path": [[author[0], author[1]], [exit_pos[0], exit_pos[1]], [target[0], target[1]]]}
            )
            continue

        # sabotage
        if target in enemy_positions:
            clean_commands.append(
                {"path": [[author[0], author[1]], [exit_pos[0], exit_pos[1]], [target[0], target[1]]]}
            )
            continue

        # beaver attack
        if target in beaver_positions:
            clean_commands.append(
                {"path": [[author[0], author[1]], [exit_pos[0], exit_pos[1]], [target[0], target[1]]]}
            )
            continue

        # build on any empty visible non-mountain cell
        if target not in own_positions and target not in enemy_positions and target not in beaver_positions:
            clean_commands.append(
                {"path": [[author[0], author[1]], [exit_pos[0], exit_pos[1]], [target[0], target[1]]]}
            )
            continue

    if clean_commands:
        clean["command"] = clean_commands

    # relocateMain
    relocate = payload.get("relocateMain")
    if isinstance(relocate, list) and len(relocate) == 2:
        try:
            a = to_coord(relocate[0])
            b = to_coord(relocate[1])
            if a in controllable_positions and b in controllable_positions and abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1:
                clean["relocateMain"] = [[a[0], a[1]], [b[0], b[1]]]
        except Exception:
            pass

    return clean


def has_useful_action(payload: Dict[str, Any]) -> bool:
    return bool(
        payload.get("command")
        or payload.get("plantationUpgrade")
        or payload.get("relocateMain")
    )


def main() -> None:
    client = ApiClient()
    bot = build_bot()
    limiter = SlidingWindowRateLimiter(max_requests=3, period_seconds=1.2)

    last_posted_turn: Optional[int] = None
    next_poll_ts = 0.0
    backoff = 0.0

    while True:
        try:
            now = time.monotonic()
            if now < next_poll_ts:
                time.sleep(min(0.2, next_poll_ts - now))
                continue

            limiter.wait_for_slot()
            arena = client.get_arena()

            turn_no = int(arena["turnNo"])
            next_turn_in = float(arena.get("nextTurnIn", 1.0))
            backoff = 0.0

            if last_posted_turn == turn_no:
                next_poll_ts = time.monotonic() + max(0.12, next_turn_in - 0.08)
                continue

            raw_payload = bot.choose_command(arena)
            if not isinstance(raw_payload, dict):
                raise RuntimeError("Бот вернул не dict")

            payload = sanitize_payload(raw_payload, arena)

            if not has_useful_action(payload):
                logging.warning(
                    "TURN %s | next=%.2fs\n"
                    "  ACTIONS:\n"
                    "    NO_VALID_ACTIONS_AFTER_SANITIZE\n"
                    "  RAW:\n"
                    "    %s",
                    turn_no,
                    next_turn_in,
                    format_payload_pretty(arena, raw_payload),
                )
                next_poll_ts = time.monotonic() + max(0.12, next_turn_in - 0.08)
                continue

            limiter.wait_for_slot()
            response = client.post_command(payload)

            pretty_payload = format_payload_pretty(arena, payload)
            pretty_response = format_response_pretty(response)

            if response_has_duplicate_submit(response):
                logging.warning(
                    "TURN %s | next=%.2fs\n"
                    "  ACTIONS:\n"
                    "    %s\n"
                    "  RESULT: %s",
                    turn_no,
                    next_turn_in,
                    pretty_payload,
                    pretty_response,
                )
            elif response_has_invalid_command(response):
                logging.warning(
                    "TURN %s | next=%.2fs\n"
                    "  ACTIONS:\n"
                    "    %s\n"
                    "  RESULT: %s",
                    turn_no,
                    next_turn_in,
                    pretty_payload,
                    pretty_response,
                )
            else:
                logging.info(
                    "TURN %s | next=%.2fs\n"
                    "  ACTIONS:\n"
                    "    %s\n"
                    "  RESULT: %s",
                    turn_no,
                    next_turn_in,
                    pretty_payload,
                    pretty_response,
                )

            last_posted_turn = turn_no
            next_poll_ts = time.monotonic() + max(0.12, next_turn_in - 0.08)

        except KeyboardInterrupt:
            logging.info("Остановлено вручную")
            break

        except Exception as exc:
            if is_rate_limit_error(exc):
                backoff = 1.0 if backoff <= 0 else min(backoff * 1.5, 4.0)
                logging.warning("Rate limit. Sleep %.2fs", backoff)
                next_poll_ts = time.monotonic() + backoff
            else:
                logging.exception("Ошибка в цикле: %s", exc)
                next_poll_ts = time.monotonic() + 1.0


if __name__ == "__main__":
    main()