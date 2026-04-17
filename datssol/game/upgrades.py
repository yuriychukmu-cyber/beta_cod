from datssol.constants import GC
from datssol.game.models import PlayerStats


def upgrade_level(player: PlayerStats, key: str) -> int:
    return player.upgrades.get(key, 0)


def effective_mhp(player: PlayerStats) -> int:
    return GC.base_mhp + 5 * upgrade_level(player, "max_hp")


def effective_rs(player: PlayerStats) -> int:
    return GC.base_rs + upgrade_level(player, "repair_power")


def effective_limit(player: PlayerStats) -> int:
    return GC.default_settlement_limit + 2 * upgrade_level(player, "settlement_limit")
