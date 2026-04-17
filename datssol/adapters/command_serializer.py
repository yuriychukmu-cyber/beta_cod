from datssol.game.commands import TurnCommand


def serialize_turn_command(cmd: TurnCommand) -> dict:
    return {
        "player_id": cmd.player_id,
        "actions": [{"path": [a.author_id, a.exit_id, a.target]} for a in cmd.actions],
        "upgrade": cmd.upgrade,
        "relocate_main_to": cmd.relocate_main_to,
    }
