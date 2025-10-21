import random
from typing import List, Optional, Tuple

from .models import (
    Tournament,
    TournamentParticipant,
    TournamentRound,
    TournamentMatch,
    RallyTriad,
    FootballGroup,
    FootballTeam,
    FootballGroupMatch,
)


def shuffle_participants(participants: List[TournamentParticipant]) -> List[TournamentParticipant]:
    shuffled = list(participants)
    random.shuffle(shuffled)
    return shuffled


def get_round_name(total_participants: int, round_index: int) -> str:
    rounds: List[str] = []
    participants = total_participants
    while participants > 2:
        if participants <= 32 and participants > 16:
            rounds.append('Dieciseisavos')
        elif participants <= 16 and participants > 8:
            rounds.append('Octavos')
        elif participants <= 8 and participants > 4:
            rounds.append('Cuartos')
        elif participants <= 4 and participants > 2:
            rounds.append('Semifinales')
        else:
            rounds.append(f'Ronda {len(rounds) + 1}')
        participants = (participants + 1) // 2
    return rounds[round_index] if round_index < len(rounds) else f'Ronda {round_index + 1}'


def create_initial_round(tournament: Tournament) -> TournamentRound:
    participants = [p for p in tournament.participants.all()]
    shuffled = shuffle_participants(participants)
    matches: List[Tuple[Optional[TournamentParticipant], Optional[TournamentParticipant], bool]] = []

    # BYE en caso de impar
    if len(shuffled) % 2 == 1:
        bye = shuffled.pop()
        matches.append((bye, None, True))

    for i in range(0, len(shuffled), 2):
        a = shuffled[i]
        b = shuffled[i + 1]
        matches.append((a, b, False))

    round_obj = TournamentRound.objects.create(
        tournament=tournament,
        index=0,
        nombre=get_round_name(len(participants), 0),
        completed=False,
    )
    for a, b, is_bye in matches:
        match = TournamentMatch.objects.create(
            round=round_obj,
            a=a if a else None,
            b=b if b else None,
            is_bye=is_bye,
        )
        if is_bye and a:
            match.winner = a
            match.save()
    return round_obj


def create_initial_round_with_participants(tournament: Tournament, participants: List[TournamentParticipant]) -> TournamentRound:
    shuffled = shuffle_participants(participants)
    pairs: List[Tuple[Optional[TournamentParticipant], Optional[TournamentParticipant], bool]] = []

    if len(shuffled) % 2 == 1:
        bye = shuffled.pop()
        pairs.append((bye, None, True))

    for i in range(0, len(shuffled), 2):
        pairs.append((shuffled[i], shuffled[i + 1], False))

    round_obj = TournamentRound.objects.create(
        tournament=tournament,
        index=0,
        nombre=get_round_name(len(participants), 0),
        completed=False,
    )
    for a, b, is_bye in pairs:
        match = TournamentMatch.objects.create(round=round_obj, a=a if a else None, b=b if b else None, is_bye=is_bye)
        if is_bye and a:
            match.winner = a
            match.save()
    return round_obj


def generate_next_round(tournament: Tournament) -> Optional[TournamentRound]:
    current_round = tournament.rounds.order_by('-index').first()
    if current_round is None:
        return None

    winners: List[TournamentParticipant] = []
    for m in current_round.matches.all():
        if m.is_bye and m.a:
            winners.append(m.a)
        elif m.winner:
            winners.append(m.winner)

    if len(winners) <= 1:
        return None

    if len(winners) == 2:
        next_round = TournamentRound.objects.create(
            tournament=tournament,
            index=current_round.index + 1,
            nombre='Final - Oro',
            completed=False,
        )
        TournamentMatch.objects.create(round=next_round, a=winners[0], b=winners[1])
        return next_round

    random.shuffle(winners)
    next_round = TournamentRound.objects.create(
        tournament=tournament,
        index=current_round.index + 1,
        nombre=get_round_name(len(winners), next_round_index_hint(current_round.index + 1)),
        completed=False,
    )
    # Si cantidad impar de ganadores, dar BYE al último
    bye_participant = None
    if len(winners) % 2 == 1:
        bye_participant = winners.pop()
    for i in range(0, len(winners), 2):
        a = winners[i]
        b = winners[i + 1]
        TournamentMatch.objects.create(round=next_round, a=a, b=b)
    if bye_participant is not None:
        bye_match = TournamentMatch.objects.create(round=next_round, a=bye_participant, b=None, is_bye=True)
        bye_match.winner = bye_participant
        bye_match.save()
    return next_round


def next_round_index_hint(idx: int) -> int:
    return idx


def create_football_groups(tournament: Tournament, max_group_size: int = 5) -> None:
    teams = list(tournament.participants.all())
    if not teams:
        return
    num_groups = (len(teams) + max_group_size - 1) // max_group_size
    for g in range(num_groups):
        codigo = chr(65 + g)  # 'A', 'B', ...
        grp = FootballGroup.objects.create(tournament=tournament, codigo=codigo)
        slice_teams = teams[g * max_group_size:(g + 1) * max_group_size]
        ft_teams: List[FootballTeam] = []
        for p in slice_teams:
            ft_teams.append(FootballTeam.objects.create(group=grp, participant=p))
        # todos contra todos
        for i in range(len(ft_teams)):
            for j in range(i + 1, len(ft_teams)):
                FootballGroupMatch.objects.create(group=grp, home=ft_teams[i], away=ft_teams[j], played=False)


def record_group_result(match: FootballGroupMatch, goals_home: int, goals_away: int) -> None:
    match.goals_home = goals_home
    match.goals_away = goals_away
    match.played = True
    match.save()

    home = match.home
    away = match.away
    # actualizar stats
    home.pj += 1
    away.pj += 1
    home.gf += goals_home
    home.gc += goals_away
    away.gf += goals_away
    away.gc += goals_home
    home.dg = home.gf - home.gc
    away.dg = away.gf - away.gc
    if goals_home > goals_away:
        home.g += 1
        away.p += 1
        home.pts += 3
    elif goals_home < goals_away:
        away.g += 1
        home.p += 1
        away.pts += 3
    else:
        home.e += 1
        away.e += 1
        home.pts += 1
        away.pts += 1
    home.save()
    away.save()
    

def are_all_group_matches_played(tournament: Tournament) -> bool:
    groups = tournament.football_groups.all()
    if not groups.exists():
        return False
    for g in groups:
        for m in g.matches.all():
            if not m.played:
                return False
    return True


def get_group_top_two(group: FootballGroup) -> List[FootballTeam]:
    # Order explicitly to avoid relying solely on Meta ordering
    return list(group.teams.order_by('-pts', '-dg', '-gf', 'participant__nombre')[:2])


def seed_knockout_from_groups(tournament: Tournament) -> Optional[TournamentRound]:
    # Do nothing if rounds already exist
    if tournament.rounds.exists():
        return None
    groups = list(tournament.football_groups.order_by('codigo').all())
    if not groups:
        return None
    # Collect top-2 from every group, ordered by tournament seeding rules
    qualified: List[TournamentParticipant] = []
    for g in groups:
        top_two = get_group_top_two(g)
        for team in top_two:
            qualified.append(team.participant)
    if not qualified:
        return None
    # Create initial knockout round with all qualified, shuffling and handling BYEs as needed
    return create_initial_round_with_participants(tournament, qualified)


def truncate_rounds_after(tournament: Tournament, base_index: int) -> None:
    """Delete all rounds with index greater than base_index to allow regeneration."""
    rounds_to_delete = tournament.rounds.filter(index__gt=base_index)
    # Cascade will remove matches
    for r in rounds_to_delete:
        r.delete()


def regenerate_following_from(tournament: Tournament, base_round: TournamentRound) -> None:
    """After editing winners in base_round, remove later rounds and rebuild chain."""
    truncate_rounds_after(tournament, base_round.index)
    # Only build subsequent rounds when current round is completed
    if all(m.is_bye or m.winner_id for m in base_round.matches.all()):
        base_round.completed = True
        base_round.save()
        # Generate chain until cannot
        while True:
            nxt = generate_next_round(tournament)
            if nxt is None:
                break

# =========================
# Rally helpers (triadas)
# =========================

def create_rally_triads(tournament: Tournament) -> None:
    participants = list(tournament.participants.all())
    if not participants:
        return
    import random
    random.shuffle(participants)
    RallyTriad.objects.filter(tournament=tournament).delete()
    idx = 0
    for i in range(0, len(participants), 3):
        triad_part = participants[i:i+3]
        # Completar con None si faltan
        a = triad_part[0] if len(triad_part) > 0 else None
        b = triad_part[1] if len(triad_part) > 1 else None
        c = triad_part[2] if len(triad_part) > 2 else None
        RallyTriad.objects.create(tournament=tournament, index=idx, a=a, b=b, c=c)
        idx += 1

def rally_triads_completed(tournament: Tournament) -> bool:
    triads = RallyTriad.objects.filter(tournament=tournament)
    if not triads.exists():
        return False
    for t in triads:
        if t.winner_id is None:
            return False
    return True

def seed_semifinals_from_triads(tournament: Tournament) -> Optional[TournamentRound]:
    if tournament.rounds.exists():
        return None
    winners = list(
        TournamentParticipant.objects.filter(
            id__in=RallyTriad.objects.filter(tournament=tournament, winner__isnull=False).values_list('winner_id', flat=True)
        )
    )
    if len(winners) < 2:
        return None
    import random
    random.shuffle(winners)
    # Si ganadores == 4 → semifinales; si 2 → final directa
    name = 'Semifinales' if len(winners) == 4 else 'Final - Oro'
    round_obj = TournamentRound.objects.create(tournament=tournament, index=0, nombre=name, completed=False)
    # Parear en 1v1, BYE si impar
    if len(winners) % 2 == 1:
        bye = winners.pop()
        m = TournamentMatch.objects.create(round=round_obj, a=bye, b=None, is_bye=True)
        m.winner = bye
        m.save()
    for i in range(0, len(winners), 2):
        TournamentMatch.objects.create(round=round_obj, a=winners[i], b=winners[i+1])
    return round_obj

