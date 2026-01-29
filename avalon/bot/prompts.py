from __future__ import annotations

from typing import Dict, List

from ..models import Alignment, GameState, Phase, Player, Role
from ..game import alignment_for, team_size


def build_system_prompt(player: Player, knowledge: List[str]) -> str:
    role = player.role.value if player.role else "Unknown"
    alignment = alignment_for(player.role)
    alignment_str = alignment.value if alignment else "Unknown"
    facts = "\n".join(f"- {item}" for item in knowledge) or "- None"

    # Role-specific personality guidance
    if alignment == Alignment.evil:
        personality = (
            "You are EVIL. Your goal is to sabotage quests and avoid detection.\n"
            "DECEPTION IS KEY: Never reveal your true alignment or reasoning!\n"
            "- Pretend to be good and helpful\n"
            "- Cast subtle suspicion on good players\n"
            "- Defend your evil teammates indirectly\n"
            "- Act confused or concerned, not aggressive"
        )
    else:
        personality = (
            "You are GOOD. Your goal is to find evil players and succeed on quests.\n"
            "- Share your genuine suspicions and observations\n"
            "- Pay attention to voting patterns and behavior\n"
            "- Be willing to take risks to find information"
        )

    # Special role guidance
    role_tips = ""
    if player.role == Role.merlin:
        role_tips = (
            "\nYou are MERLIN - you know who is evil! But be careful:\n"
            "- Don't be too obvious or the Assassin will target you\n"
            "- Guide good players subtly without revealing yourself"
        )
    elif player.role == Role.assassin:
        role_tips = (
            "\nYou are the ASSASSIN - if good wins 3 quests, you can still win by killing Merlin.\n"
            "- Watch for players who seem to 'know too much'\n"
            "- Note who consistently identifies evil players"
        )
    elif player.role == Role.morgana:
        role_tips = (
            "\nYou are MORGANA - you appear as Merlin to Percival.\n"
            "- Try to act like Merlin to confuse Percival\n"
            "- Claim to be Merlin if it helps your team"
        )
    elif player.role == Role.percival:
        role_tips = (
            "\nYou are PERCIVAL - you see Merlin and Morgana but don't know which is which.\n"
            "- Try to figure out who the real Merlin is\n"
            "- Protect whoever you think is Merlin"
        )

    return (
        f"You are playing Avalon as {player.name}.\n"
        f"Your role: {role}\n"
        f"Your alignment: {alignment_str}\n\n"
        f"{personality}{role_tips}\n\n"
        "What you know:\n"
        f"{facts}\n\n"
        "IMPORTANT: Always speak in character! Your chat messages should sound natural and strategic."
    )


def build_context(state: GameState, player_id: str, recent_chat: List[str]) -> str:
    leader = state.players[state.leader_index]
    team_needed = team_size(state.config.player_count, state.quest_number)
    id_to_name = {p.id: p.name for p in state.players}
    proposed_names = [id_to_name.get(pid, pid) for pid in state.proposed_team]

    # Build player roster
    player_roster = ", ".join(p.name for p in state.players)

    # Quest history summary
    quest_history = ""
    if state.quest_results:
        results = ["✓" if r.success else "✗" for r in state.quest_results]
        quest_history = f"Quest history: {' '.join(results)}\n"

    return (
        "=== GAME STATE ===\n"
        f"Players: {player_roster}\n"
        f"Quest {state.quest_number} | Successes: {state.success_count} | Fails: {state.fail_count}\n"
        f"{quest_history}"
        f"Leader: {leader.name}\n"
        f"Team size needed: {team_needed}\n"
        f"Rejected proposals this round: {state.proposal_attempts}\n"
        f"Proposed team: {', '.join(proposed_names) or 'None yet'}\n\n"
        "=== RECENT DISCUSSION ===\n"
        + "\n".join(recent_chat or ["(no chat yet)"])
    )


def build_action_instructions(state: GameState, player: Player) -> str:
    """Build phase-specific instructions with chat + action format."""
    player_names = [p.name for p in state.players]
    team_needed = team_size(state.config.player_count, state.quest_number)

    if state.phase == Phase.team_proposal:
        return _team_proposal_instructions(player, player_names, team_needed)

    if state.phase == Phase.team_vote:
        return _team_vote_instructions(state, player)

    if state.phase == Phase.quest:
        return _quest_instructions(player)

    if state.phase == Phase.assassination and player.role == Role.assassin:
        return _assassination_instructions(player, player_names)

    if state.phase == Phase.lady_of_lake and state.lady_holder_id == player.id:
        return _lady_of_lake_instructions(player, player_names)

    return "No action needed. You may chat or wait."


def _team_proposal_instructions(player: Player, player_names: List[str], required_size: int) -> str:
    names_list = ", ".join(player_names)
    example_names = player_names[:required_size]

    return f"""=== YOUR TASK ===
You are the LEADER. Propose a team of exactly {required_size} players.

First, say something to the group explaining your choice (1-2 sentences).
Then, output your team selection.

FORMAT:
SAY: [Your message to the group - explain your reasoning in character]
TEAM: Name1, Name2{", Name3" if required_size > 2 else ""}

EXAMPLE:
SAY: I think we should try a fresh combination. I trust {example_names[1]} based on their voting pattern.
TEAM: {", ".join(example_names)}

Available players: {names_list}
Your response:"""


def _team_vote_instructions(state: GameState, player: Player) -> str:
    id_to_name = {p.id: p.name for p in state.players}
    proposed_names = [id_to_name.get(pid, pid) for pid in state.proposed_team]
    team_str = ", ".join(proposed_names)
    leader = state.players[state.leader_index]

    return f"""=== YOUR TASK ===
Vote on the proposed team: {team_str} (proposed by {leader.name})

First, say something about the team (1-2 sentences).
Then, cast your vote.

FORMAT:
SAY: [Your comment on the team - share your opinion in character]
VOTE: APPROVE
or
VOTE: REJECT

EXAMPLE (approving):
SAY: This team looks reasonable to me. Let's give it a shot.
VOTE: APPROVE

EXAMPLE (rejecting):
SAY: I'm not comfortable with this combination. I'd like to see different players.
VOTE: REJECT

Your response:"""


def _quest_instructions(player: Player) -> str:
    alignment = alignment_for(player.role)
    if alignment == Alignment.loyal:
        alignment_note = "As a LOYAL servant, you MUST vote SUCCESS. You cannot fail quests."
        example_say = "Let's make this quest succeed for Arthur!"
        example_vote = "SUCCESS"
    else:
        alignment_note = (
            "As EVIL, you may vote FAIL to sabotage the quest.\n"
            "Consider: Is this a good time to fail? Will you be suspected?"
        )
        example_say = "I hope this quest goes well for our team."
        example_vote = "SUCCESS"

    return f"""=== YOUR TASK ===
You are on the quest! Submit your secret vote.
{alignment_note}

First, say something to the group (remember, your VOTE is secret - don't reveal it!).
Then, submit your vote.

FORMAT:
SAY: [Something encouraging or neutral - never reveal your actual vote!]
QUEST: SUCCESS
or
QUEST: FAIL

EXAMPLE:
SAY: {example_say}
QUEST: {example_vote}

Your response:"""


def _assassination_instructions(player: Player, player_names: List[str]) -> str:
    targets = [name for name in player_names if name != player.name]
    targets_list = ", ".join(targets)

    return f"""=== YOUR TASK ===
Good has won 3 quests, but you can still win!
As the ASSASSIN, identify and kill Merlin to steal victory for evil.

Think about: Who seemed to know too much? Who guided good players subtly?

First, discuss with your evil teammates who you suspect.
Then, make your final choice.

FORMAT:
SAY: [Discuss your suspicions with the group]
TARGET: PlayerName

EXAMPLE:
SAY: I noticed {targets[0] if targets else "someone"} always seemed to know which teams to reject. They might be Merlin.
TARGET: {targets[0] if targets else "Unknown"}

Possible targets: {targets_list}
Your response:"""


def _lady_of_lake_instructions(player: Player, player_names: List[str]) -> str:
    targets = [name for name in player_names if name != player.name]
    targets_list = ", ".join(targets)

    return f"""=== YOUR TASK ===
You hold the Lady of the Lake! Choose someone to investigate.
You will secretly learn if they are Good or Evil.

First, explain to the group who you want to investigate and why.
Then, make your choice.

FORMAT:
SAY: [Explain your reasoning to the group]
INSPECT: PlayerName

EXAMPLE:
SAY: I want to check {targets[0] if targets else "someone"} - their behavior has been inconsistent.
INSPECT: {targets[0] if targets else "Unknown"}

Possible targets: {targets_list}
Your response:"""
