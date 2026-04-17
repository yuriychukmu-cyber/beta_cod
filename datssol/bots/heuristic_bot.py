from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

Coord = Tuple[int, int]


class HeuristicBot:
    """
    Wave-expansion bot.

    Идея:
    1. ЦУ всегда должно иметь страховочную сеть рядом.
    2. Каждая плантация по возможности строит соседнюю клетку.
    3. Если автор уже начал стройку — он продолжает ее, а не бросает.
    4. Растем "волной" от центра сети.
    5. Легкий приоритет к boosted-клеткам (x,y кратны 7).
    6. Лупы/замыкания лучше длинных хрупких веток.
    """

    def __init__(self) -> None:
        self.last_target_by_author: Dict[Coord, Coord] = {}
        self.repeat_count_by_author: Dict[Coord, int] = {}

    # ------------------------------------------------------------
    # Public
    # ------------------------------------------------------------
    def choose_command(self, arena: Dict[str, Any]) -> Dict[str, Any]:
        state = self._parse_state(arena)

        payload: Dict[str, Any] = {}

        relocate = self._select_relocate_main(state)
        if relocate is not None:
            payload["relocateMain"] = [
                [relocate[0][0], relocate[0][1]],
                [relocate[1][0], relocate[1][1]],
            ]

        upgrade = self._select_upgrade(state)
        if upgrade:
            payload["plantationUpgrade"] = upgrade

        commands = self._build_commands(state)
        if commands:
            payload["command"] = commands

        if not self._has_useful_action(payload):
            payload = self._fallback_payload(state)

        self._update_memory(payload)
        return payload

    # ------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------
    def _parse_state(self, arena: Dict[str, Any]) -> Dict[str, Any]:
        own_all = [self._norm_plantation(p) for p in (arena.get("plantations", []) or [])]
        controllable = [p for p in own_all if not p.get("isIsolated", False)]

        own_positions = {p["position"] for p in own_all}
        controllable_positions = {p["position"] for p in controllable}

        enemy_positions = {self._to_coord(e["position"]) for e in (arena.get("enemy", []) or [])}
        beaver_positions = {self._to_coord(b["position"]) for b in (arena.get("beavers", []) or [])}
        mountains = {self._to_coord(m) for m in (arena.get("mountains", []) or [])}

        construction_by_pos = {
            self._to_coord(c["position"]): {
                "position": self._to_coord(c["position"]),
                "progress": int(c.get("progress", 0)),
            }
            for c in (arena.get("construction", []) or [])
        }
        construction_positions = set(construction_by_pos.keys())

        cells_by_pos = {
            self._to_coord(c["position"]): {
                "position": self._to_coord(c["position"]),
                "terraformationProgress": float(c.get("terraformationProgress", 0.0)),
                "turnsUntilDegradation": int(c.get("turnsUntilDegradation", 0)),
            }
            for c in (arena.get("cells", []) or [])
        }

        upgrades = arena.get("plantationUpgrades", {}) or {}
        tiers = {
            t["name"]: t
            for t in (upgrades.get("tiers", []) or [])
            if isinstance(t, dict) and "name" in t
        }

        repair_level = int(tiers.get("repair_power", {}).get("current", 0))
        settlement_level = int(tiers.get("settlement_limit", {}).get("current", 0))
        signal_level = int(tiers.get("signal_range", {}).get("current", 0))
        max_hp_level = int(tiers.get("max_hp", {}).get("current", 0))

        build_power = 5 + repair_level
        max_hp = 50 + 10 * max_hp_level
        settlement_limit = 30 + settlement_level
        signal_range = 3 + signal_level

        main_obj = next((p for p in own_all if p.get("isMain", False)), None)
        main_pos = main_obj["position"] if main_obj else None
        main_hp = int(main_obj.get("hp", max_hp)) if main_obj else max_hp

        main_progress = 0.0
        if main_pos is not None and main_pos in cells_by_pos:
            main_progress = float(cells_by_pos[main_pos].get("terraformationProgress", 0.0))

        width = int((arena.get("size", [0, 0]) or [0, 0])[0])
        height = int((arena.get("size", [0, 0]) or [0, 0])[1])
        action_range = int(arena.get("actionRange", 2))
        upgrade_points = int(upgrades.get("points", 0))

        forecasts = [dict(f) for f in (arena.get("meteoForecasts", []) or [])]
        earthquake_soon = any(
            f.get("kind") == "earthquake" and int(f.get("turnsUntil", 99)) <= 1
            for f in forecasts
        )

        degree = {pos: self._degree(pos, controllable_positions) for pos in controllable_positions}
        articulation_points = self._articulation_points(controllable_positions)

        network_center = self._network_center(controllable_positions, main_pos)

        return {
            "turn_no": int(arena.get("turnNo", 0)),
            "width": width,
            "height": height,
            "action_range": action_range,
            "upgrade_points": upgrade_points,
            "tiers": tiers,
            "build_power": build_power,
            "max_hp": max_hp,
            "settlement_limit": settlement_limit,
            "signal_range": signal_range,
            "own_all": own_all,
            "controllable": controllable,
            "own_positions": own_positions,
            "controllable_positions": controllable_positions,
            "enemy_positions": enemy_positions,
            "beaver_positions": beaver_positions,
            "mountains": mountains,
            "construction_by_pos": construction_by_pos,
            "construction_positions": construction_positions,
            "cells_by_pos": cells_by_pos,
            "forecasts": forecasts,
            "earthquake_soon": earthquake_soon,
            "main_obj": main_obj,
            "main_pos": main_pos,
            "main_hp": main_hp,
            "main_progress": main_progress,
            "degree": degree,
            "articulation_points": articulation_points,
            "network_center": network_center,
        }

    # ------------------------------------------------------------
    # Build commands
    # ------------------------------------------------------------
    def _build_commands(self, state: Dict[str, Any]) -> List[Dict[str, List[List[int]]]]:
        authors = sorted(
            state["controllable"],
            key=lambda p: (
                not p.get("isMain", False),
                state["degree"].get(p["position"], 0),
                -self._manhattan(p["position"], state["network_center"]),
            ),
        )

        used_authors: Set[Coord] = set()
        used_targets: Set[Coord] = set()
        commands: List[Dict[str, List[List[int]]]] = []

        # 1. emergency ring around main
        emergency_targets = self._main_emergency_targets(state)
        for target in emergency_targets:
            nearest = self._best_author_for_target(state, authors, target, used_authors)
            if nearest is not None:
                commands.append(self._build_path(nearest, nearest, target))
                used_authors.add(nearest)
                used_targets.add(target)

        # 2. authors continue their own started constructions
        for author_obj in authors:
            author = author_obj["position"]
            if author in used_authors:
                continue

            target = self.last_target_by_author.get(author)
            if target is None:
                continue
            if target not in state["construction_positions"]:
                continue
            if not self._in_square_range(author, target, state["action_range"]):
                continue
            if target in used_targets:
                continue
            if self._too_dangerous(target, state):
                continue

            commands.append(self._build_path(author, author, target))
            used_authors.add(author)
            used_targets.add(target)

        # 3. each remaining plantation starts/extends its own neighboring wave
        for author_obj in authors:
            author = author_obj["position"]
            if author in used_authors:
                continue

            target = self._best_wave_target_for_author(state, author, used_targets)
            if target is None:
                continue

            commands.append(self._build_path(author, author, target))
            used_authors.add(author)
            used_targets.add(target)

        # 4. if nobody built, try repair critical nodes
        if not commands:
            repairs = self._repair_fallbacks(state)
            for author, target in repairs:
                commands.append(self._build_path(author, author, target))

        return commands

    def _best_wave_target_for_author(
        self,
        state: Dict[str, Any],
        author: Coord,
        used_targets: Set[Coord],
    ) -> Optional[Coord]:
        candidates = []

        # A) if author already has a started construction nearby and not busy elsewhere
        last_target = self.last_target_by_author.get(author)
        if (
            last_target is not None
            and last_target in state["construction_positions"]
            and self._in_square_range(author, last_target, state["action_range"])
            and last_target not in used_targets
            and not self._too_dangerous(last_target, state)
        ):
            return last_target

        # B) new neighboring cells: only adj4 for wave pattern
        for target in self._adj4_positions(author):
            if not self._in_bounds(target, state["width"], state["height"]):
                continue
            if target in used_targets:
                continue
            if target in state["mountains"]:
                continue
            if target in state["enemy_positions"]:
                continue
            if target in state["beaver_positions"]:
                continue
            if target in state["own_positions"]:
                continue

            score = self._score_wave_target(state, author, target)
            if score > -10**12:
                candidates.append((score, target))

        # C) if nothing adj4, allow any cell in action range that still keeps wave feeling
        if not candidates:
            for target in self._iter_targets_in_range(author, state["action_range"], state["width"], state["height"]):
                if target in used_targets:
                    continue
                if target in state["mountains"]:
                    continue
                if target in state["enemy_positions"]:
                    continue
                if target in state["beaver_positions"]:
                    continue
                if target in state["own_positions"]:
                    continue

                score = self._score_wave_target(state, author, target) - 120.0
                if score > -10**12:
                    candidates.append((score, target))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def _score_wave_target(self, state: Dict[str, Any], author: Coord, target: Coord) -> float:
        # must stay connected to network
        adj_own = sum(1 for p in state["own_positions"] if self._is_adj4(p, target))
        adj_construction = sum(1 for p in state["construction_positions"] if self._is_adj4(p, target))

        if adj_own + adj_construction == 0:
            return -10**18

        score = 0.0

        # 1) outward wave from center
        center = state["network_center"]
        score += 18.0 * self._manhattan(target, center)

        # 2) boosted preference
        if self._is_boosted(target):
            score += 260.0
        else:
            score += self._boost_proximity_bonus(target)

        # 3) prefer cells that create more stable structure
        if adj_own >= 2:
            score += 180.0
        elif adj_own == 1:
            score += 60.0

        if adj_construction >= 1:
            score += 25.0

        # 4) if author is articulation / fragile branch, prefer loop closing
        author_degree = state["degree"].get(author, 0)
        if author in state["articulation_points"] or author_degree <= 1:
            if adj_own >= 2:
                score += 140.0
            else:
                score -= 80.0

        # 5) keep direction consistent for this author
        last_target = self.last_target_by_author.get(author)
        repeats = self.repeat_count_by_author.get(author, 0)
        if last_target == target:
            score -= 60.0 * min(repeats, 4)

        # 6) avoid danger
        if self._in_beaver_fire(target, state["beaver_positions"]):
            score -= 240.0
        if self._in_storm_risk(target, state["forecasts"]):
            score -= 150.0

        # 7) small bias away from main when network already safe
        main_pos = state["main_pos"]
        if main_pos is not None:
            live_ring = sum(1 for nb in self._adj4_positions(main_pos) if nb in state["own_positions"])
            if live_ring >= 2:
                score += 6.0 * self._manhattan(target, main_pos)

        return score

    # ------------------------------------------------------------
    # Emergency / relocate
    # ------------------------------------------------------------
    def _main_emergency_targets(self, state: Dict[str, Any]) -> List[Coord]:
        main_pos = state["main_pos"]
        if main_pos is None:
            return []

        live_ring = [nb for nb in self._adj4_positions(main_pos) if nb in state["own_positions"]]
        cons_ring = [nb for nb in self._adj4_positions(main_pos) if nb in state["construction_positions"]]

        need_ring = len(live_ring) + len(cons_ring) < 2
        need_escape = state["main_progress"] >= 78.0

        if not need_ring and not need_escape:
            return []

        candidates = []
        for nb in self._adj4_positions(main_pos):
            if not self._in_bounds(nb, state["width"], state["height"]):
                continue
            if nb in state["mountains"]:
                continue
            if nb in state["enemy_positions"]:
                continue
            if nb in state["beaver_positions"]:
                continue
            if nb in state["own_positions"]:
                continue

            score = 1000.0
            if nb in state["construction_positions"]:
                score += 300.0 + 5.0 * int(state["construction_by_pos"][nb]["progress"])
            if self._is_boosted(nb):
                score += 80.0

            adj_own = sum(1 for p in state["own_positions"] if self._is_adj4(p, nb))
            score += 70.0 * adj_own

            candidates.append((score, nb))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates[:2]]

    def _select_relocate_main(self, state: Dict[str, Any]) -> Optional[Tuple[Coord, Coord]]:
        main_pos = state["main_pos"]
        if main_pos is None:
            return None

        if state["main_progress"] < 82.0:
            return None

        candidates = []
        for nb in self._adj4_positions(main_pos):
            if nb not in state["own_positions"]:
                continue

            progress = 0.0
            if nb in state["cells_by_pos"]:
                progress = float(state["cells_by_pos"][nb].get("terraformationProgress", 0.0))

            score = 1000.0
            score -= progress * 10.0
            score += 40.0 * self._degree(nb, state["own_positions"])

            if nb in state["articulation_points"]:
                score += 50.0

            candidates.append((score, nb))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        return main_pos, candidates[0][1]

    # ------------------------------------------------------------
    # Upgrades
    # ------------------------------------------------------------
    def _select_upgrade(self, state: Dict[str, Any]) -> Optional[str]:
        if state["upgrade_points"] <= 0:
            return None

        tiers = state["tiers"]

        own_count = len(state["own_positions"])
        construction_count = len(state["construction_positions"])
        free_slots = state["settlement_limit"] - (own_count + construction_count)

        repair_level = int(tiers.get("repair_power", {}).get("current", 0))
        signal_level = int(tiers.get("signal_range", {}).get("current", 0))
        settlement_level = int(tiers.get("settlement_limit", {}).get("current", 0))
        max_hp_level = int(tiers.get("max_hp", {}).get("current", 0))

        # maximize plantation count first
        if free_slots <= 3 and self._can_upgrade(tiers, "settlement_limit"):
            return "settlement_limit"

        # early acceleration
        if repair_level < 2 and self._can_upgrade(tiers, "repair_power"):
            return "repair_power"

        if own_count >= 6 and signal_level < 1 and self._can_upgrade(tiers, "signal_range"):
            return "signal_range"

        if free_slots <= 5 and self._can_upgrade(tiers, "settlement_limit"):
            return "settlement_limit"

        if repair_level < 3 and self._can_upgrade(tiers, "repair_power"):
            return "repair_power"

        if own_count >= 10 and signal_level < 2 and self._can_upgrade(tiers, "signal_range"):
            return "signal_range"

        # situational defense
        main_pos = state["main_pos"]
        if main_pos is not None and self._in_beaver_fire(main_pos, state["beaver_positions"]):
            if self._can_upgrade(tiers, "beaver_damage_mitigation"):
                return "beaver_damage_mitigation"

        if state["earthquake_soon"] and own_count >= 10:
            if self._can_upgrade(tiers, "earthquake_mitigation"):
                return "earthquake_mitigation"

        # hp only later
        if own_count >= 12 and max_hp_level < 2 and self._can_upgrade(tiers, "max_hp"):
            return "max_hp"

        for name in [
            "settlement_limit",
            "repair_power",
            "signal_range",
            "vision_range",
            "beaver_damage_mitigation",
            "earthquake_mitigation",
            "decay_mitigation",
            "max_hp",
        ]:
            if self._can_upgrade(tiers, name):
                return name

        return None

    # ------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------
    def _fallback_payload(self, state: Dict[str, Any]) -> Dict[str, Any]:
        main_pos = state["main_pos"]
        if main_pos is not None:
            for nb in self._adj4_positions(main_pos):
                if not self._in_bounds(nb, state["width"], state["height"]):
                    continue
                if nb in state["mountains"]:
                    continue
                if nb in state["enemy_positions"]:
                    continue
                if nb in state["beaver_positions"]:
                    continue
                if nb in state["own_positions"]:
                    continue
                return {"command": [self._build_path(main_pos, main_pos, nb)]}

        upgrade = self._select_upgrade(state)
        if upgrade:
            return {"plantationUpgrade": upgrade}

        return {}

    # ------------------------------------------------------------
    # Repair fallback
    # ------------------------------------------------------------
    def _repair_fallbacks(self, state: Dict[str, Any]) -> List[Tuple[Coord, Coord]]:
        repairs: List[Tuple[Coord, Coord]] = []
        main_pos = state["main_pos"]
        if main_pos is None:
            return repairs

        for author_obj in state["controllable"]:
            author = author_obj["position"]
            if author == main_pos:
                continue
            if not self._in_square_range(author, main_pos, state["action_range"]):
                continue
            if state["main_hp"] < state["max_hp"]:
                repairs.append((author, main_pos))
                break

        return repairs

    # ------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------
    def _update_memory(self, payload: Dict[str, Any]) -> None:
        commands = payload.get("command", []) or []
        seen_authors: Set[Coord] = set()

        for cmd in commands:
            path = cmd.get("path", [])
            if len(path) != 3:
                continue

            author = self._to_coord(path[0])
            target = self._to_coord(path[2])

            if self.last_target_by_author.get(author) == target:
                self.repeat_count_by_author[author] = self.repeat_count_by_author.get(author, 0) + 1
            else:
                self.last_target_by_author[author] = target
                self.repeat_count_by_author[author] = 1

            seen_authors.add(author)

        for author in list(self.repeat_count_by_author.keys()):
            if author not in seen_authors:
                self.repeat_count_by_author[author] = 0

    # ------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------
    def _best_author_for_target(
        self,
        state: Dict[str, Any],
        authors: List[Dict[str, Any]],
        target: Coord,
        used_authors: Set[Coord],
    ) -> Optional[Coord]:
        candidates = []
        for a in authors:
            pos = a["position"]
            if pos in used_authors:
                continue
            if not self._in_square_range(pos, target, state["action_range"]):
                continue
            score = 0.0
            score -= self._manhattan(pos, target) * 2.0
            if a.get("isMain", False):
                score += 30.0
            candidates.append((score, pos))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def _network_center(self, positions: Set[Coord], main_pos: Optional[Coord]) -> Coord:
        if not positions:
            return main_pos if main_pos is not None else (0, 0)

        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        cx = round(sum(xs) / len(xs))
        cy = round(sum(ys) / len(ys))
        return (cx, cy)

    def _boost_proximity_bonus(self, pos: Coord) -> float:
        dx = min(pos[0] % 7, (7 - pos[0] % 7) % 7)
        dy = min(pos[1] % 7, (7 - pos[1] % 7) % 7)
        d = dx + dy
        return max(0.0, 90.0 - 15.0 * d)

    def _too_dangerous(self, pos: Coord, state: Dict[str, Any]) -> bool:
        if self._in_beaver_fire(pos, state["beaver_positions"]):
            return True
        return False

    def _in_beaver_fire(self, pos: Coord, beavers: Set[Coord]) -> bool:
        return any(self._in_square_range(pos, b, 2) for b in beavers)

    def _in_storm_risk(self, pos: Coord, forecasts: List[Dict[str, Any]]) -> bool:
        for f in forecasts:
            if f.get("kind") != "sandstorm":
                continue
            radius = int(f.get("radius", 0))
            cur = self._to_coord(f.get("position", [10**9, 10**9]))
            nxt = self._to_coord(f.get("nextPosition", [10**9, 10**9]))
            if self._in_square_range(pos, cur, radius) or self._in_square_range(pos, nxt, radius):
                return True
        return False

    def _degree(self, pos: Coord, positions: Set[Coord]) -> int:
        return sum(1 for nb in self._adj4_positions(pos) if nb in positions)

    def _articulation_points(self, positions: Set[Coord]) -> Set[Coord]:
        if len(positions) <= 2:
            return set()

        result: Set[Coord] = set()
        nodes = list(positions)

        for removed in nodes:
            remaining = positions - {removed}
            if len(remaining) <= 1:
                continue

            start = next(iter(remaining))
            seen = {start}
            stack = [start]

            while stack:
                cur = stack.pop()
                for nb in self._adj4_positions(cur):
                    if nb in remaining and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)

            if len(seen) != len(remaining):
                result.add(removed)

        return result

    def _norm_plantation(self, p: Dict[str, Any]) -> Dict[str, Any]:
        q = dict(p)
        q["position"] = self._to_coord(p["position"])
        q["hp"] = int(p.get("hp", 50))
        q["isMain"] = bool(p.get("isMain", False))
        q["isIsolated"] = bool(p.get("isIsolated", False))
        q["immunityUntilTurn"] = int(p.get("immunityUntilTurn", 0))
        return q

    def _build_path(self, author: Coord, exit_pos: Coord, target: Coord) -> Dict[str, List[List[int]]]:
        return {
            "path": [
                [author[0], author[1]],
                [exit_pos[0], exit_pos[1]],
                [target[0], target[1]],
            ]
        }

    def _adj4_positions(self, pos: Coord) -> Iterable[Coord]:
        x, y = pos
        yield (x + 1, y)
        yield (x - 1, y)
        yield (x, y + 1)
        yield (x, y - 1)

    def _iter_targets_in_range(self, center: Coord, radius: int, width: int, height: int) -> Iterable[Coord]:
        cx, cy = center
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                x, y = cx + dx, cy + dy
                if 0 <= x < width and 0 <= y < height:
                    yield (x, y)

    def _can_upgrade(self, tiers: Dict[str, Dict[str, Any]], name: str) -> bool:
        tier = tiers.get(name)
        if not tier:
            return False
        return int(tier.get("current", 0)) < int(tier.get("max", 0))

    @staticmethod
    def _has_useful_action(payload: Dict[str, Any]) -> bool:
        return bool(
            payload.get("command")
            or payload.get("plantationUpgrade")
            or payload.get("relocateMain")
        )

    @staticmethod
    def _to_coord(value: List[int] | Tuple[int, int]) -> Coord:
        return int(value[0]), int(value[1])

    @staticmethod
    def _manhattan(a: Coord, b: Coord) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def _is_adj4(a: Coord, b: Coord) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    @staticmethod
    def _is_boosted(pos: Coord) -> bool:
        return pos[0] % 7 == 0 and pos[1] % 7 == 0

    @staticmethod
    def _in_square_range(a: Coord, b: Coord, radius: int) -> bool:
        return abs(a[0] - b[0]) <= radius and abs(a[1] - b[1]) <= radius

    @staticmethod
    def _in_bounds(pos: Coord, width: int, height: int) -> bool:
        x, y = pos
        return 0 <= x < width and 0 <= y < height