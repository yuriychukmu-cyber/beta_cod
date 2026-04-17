from dataclasses import dataclass


@dataclass(frozen=True)
class GameConstants:
    max_turns: int = 600
    base_mhp: int = 50
    base_ts: int = 5
    base_cs: int = 5
    base_rs: int = 5
    base_se: int = 5
    base_be: int = 5
    base_ds: int = 10
    base_ar: int = 2
    base_sr: int = 3
    base_vr: int = 3
    default_settlement_limit: int = 30
    construction_threshold: int = 50
    new_plantation_immunity_turns: int = 3
    stalled_construction_damage: int = 10
    boosted_modulo: int = 7
    regular_cell_max_score: int = 1000
    boosted_cell_max_score: int = 1500
    terraform_decay_delay: int = 80
    terraform_decay_per_turn: int = 10
    beaver_lair_hp: int = 100
    beaver_lair_regen: int = 5
    beaver_attack_damage: int = 15
    beaver_attack_range: int = 2
    sandstorm_prob: float = 0.10
    earthquake_prob: float = 0.05
    sandstorm_damage: int = 2
    earthquake_damage: int = 10
    upgrade_point_every_turns: int = 30
    upgrade_max_bank: int = 15


GC = GameConstants()

ACTION_TYPES = ["noop", "build", "repair", "sabotage", "attack_beaver"]
UPGRADE_TYPES = [
    "repair_power",
    "max_hp",
    "settlement_limit",
    "signal_range",
    "vision_range",
    "decay_mitigation",
    "earthquake_mitigation",
    "beaver_damage_mitigation",
]
