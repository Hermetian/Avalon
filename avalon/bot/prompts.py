from __future__ import annotations

from typing import Dict, List

from ..models import Alignment, GameState, Phase, Player, Role
from ..game import alignment_for, team_size


def build_system_prompt(player: Player, knowledge: List[str]) -> str:
    role = player.role.value if player.role else "Unknown"
    alignment = alignment_for(player.role).value if player.role else "Unknown"
    facts = "\n".join(f"- {item}" for item in knowledge) or "- None"
    return (
        "You are a player in the game Avalon. Your goal is to win for your alignment.\n"
        f"Your role: {role}\n"
        f"Your alignment: {alignment}\n"
        "What you know:\n"
        f"{facts}\n\n"
        "Think step by step, then give your final answer in the EXACT format requested."
    )


def build_context(state: GameState, player_id: str, recent_chat: List[str]) -> str:
    leader = state.players[state.leader_index]
    team_needed = team_size(state.config.player_count, state.quest_number)
    id_to_name = {p.id: p.name for p in state.players}
    proposed_names = [id_to_name.get(pid, pid) for pid in state.proposed_team]

    # Build player roster
    player_roster = ", ".join(p.name for p in state.players)

    return (
        "=== GAME STATE ===\n"
        f"Players in game: {player_roster}\n"
        f"Current phase: {state.phase.value if hasattr(state.phase, 'value') else state.phase}\n"
        f"Quest number: {state.quest_number}\n"
        f"Current leader: {leader.name}\n"
        f"Team size needed: {team_needed}\n"
        f"Rejected proposals this round: {state.proposal_attempts}\n"
        f"Proposed team: {', '.join(proposed_names) or 'None yet'}\n"
        f"Quest results - Successes: {state.success_count} | Fails: {state.fail_count}\n"
        "Recent chat:\n"
        + "\n".join(recent_chat or ["(none)"])
    )


def build_action_instructions(state: GameState, player: Player) -> str:
    """Build phase-specific instructions with simplified format and few-shot examples."""
    # Get player names for context
    player_names = [p.name for p in state.players]
    team_needed = team_size(state.config.player_count, state.quest_number)

    if state.phase == Phase.team_proposal:
        return _team_proposal_instructions(player, player_names, team_needed)

    if state.phase == Phase.team_vote:
        return _team_vote_instructions(state)

    if state.phase == Phase.quest:
        return _quest_instructions(player)

    if state.phase == Phase.assassination and player.role == Role.assassin:
        return _assassination_instructions(player, player_names)

    if state.phase == Phase.lady_of_lake and state.lady_holder_id == player.id:
        return _lady_of_lake_instructions(player, player_names)

    return "No action needed. You may chat or wait."


def _team_proposal_instructions(player: Player, player_names: List[str], required_size: int) -> str:
    names_list = ", ".join(player_names)
    example_team = ", ".join(player_names[:required_size])

    return f"""=== YOUR TASK ===
You are the leader. Propose a team of exactly {required_size} players for this quest.

Think about who you trust and who might be evil. Then output your decision.

FORMAT: End your response with exactly:
TEAM: Name1, Name2{", Name3" if required_size > 2 else ""}

EXAMPLE:
I should include myself since I trust my own alignment. Looking at who else seems trustworthy...
TEAM: {example_team}

Available players: {names_list}
Your answer:"""


def _team_vote_instructions(state: GameState) -> str:
    id_to_name = {p.id: p.name for p in state.players}
    proposed_names = [id_to_name.get(pid, pid) for pid in state.proposed_team]
    team_str = ", ".join(proposed_names)

    return f"""=== YOUR TASK ===
Vote to APPROVE or REJECT the proposed team: {team_str}

Think about whether this team looks trustworthy. Then output your decision.

FORMAT: End your response with exactly:
VOTE: APPROVE
or
VOTE: REJECT

EXAMPLE:
This team includes players I'm suspicious of...
VOTE: REJECT

Your answer:"""


def _quest_instructions(player: Player) -> str:
    alignment = alignment_for(player.role)
    if alignment == Alignment.loyal:
        alignment_note = "As a loyal servant, you MUST vote SUCCESS."
    else:
        alignment_note = "As a minion of evil, you may choose to FAIL the quest."

    return f"""=== YOUR TASK ===
You are on the quest team. Submit your quest vote.
{alignment_note}

FORMAT: End your response with exactly:
QUEST: SUCCESS
or
QUEST: FAIL

EXAMPLE:
I need to consider what's best for my team...
QUEST: SUCCESS

Your answer:"""


def _assassination_instructions(player: Player, player_names: List[str]) -> str:
    # Exclude the assassin from targets
    targets = [name for name in player_names if name != player.name]
    targets_list = ", ".join(targets)

    return f"""=== YOUR TASK ===
The good team has won 3 quests! As the Assassin, you have one chance to win.
If you correctly identify and assassinate Merlin, evil wins!

Think about who has been acting like they have special knowledge. Then choose your target.

FORMAT: End your response with exactly:
TARGET: PlayerName

EXAMPLE:
That player seemed to know too much about evil players...
TARGET: {targets[0] if targets else "Unknown"}

Possible targets: {targets_list}
Your answer:"""


def _lady_of_lake_instructions(player: Player, player_names: List[str]) -> str:
    # Exclude self from targets
    targets = [name for name in player_names if name != player.name]
    targets_list = ", ".join(targets)

    return f"""=== YOUR TASK ===
You hold the Lady of the Lake. Choose a player to inspect their alignment.
You will learn if they are Good or Evil.

FORMAT: End your response with exactly:
INSPECT: PlayerName

EXAMPLE:
I want to know more about that suspicious player...
INSPECT: {targets[0] if targets else "Unknown"}

Possible targets: {targets_list}
Your answer:"""
