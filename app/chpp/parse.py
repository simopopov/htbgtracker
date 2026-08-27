"""Parsers for the CHPP XML files this project consumes.

Element paths follow the documented file structures; the mock fixtures mirror
them exactly. Before production, diff each parser against a real response —
CHPP versions occasionally move elements.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

SKILL_TAGS = {
    "stamina": "StaminaSkill",
    "goalkeeping": "KeeperSkill",
    "defending": "DefenderSkill",
    "playmaking": "PlaymakerSkill",
    "winger": "WingerSkill",
    "passing": "PassingSkill",
    "scoring": "ScorerSkill",
    "set_pieces": "SetPiecesSkill",
}


def _t(el, path, default=None):
    found = el.find(path)
    if found is not None and found.text is not None:
        return found.text.strip()
    return default


def _i(el, path, default=None):
    v = _t(el, path)
    if v in (None, ""):
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _b(el, path, default=False):
    v = _t(el, path)
    if v is None:
        return default
    return v.lower() in ("true", "1")


def _dt(el, path):
    v = _t(el, path)
    if not v:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


def _first_int(el, *paths):
    for path in paths:
        value = _i(el, path)
        if value is not None:
            return value
    return None


def parse_error(root: ET.Element):
    """Return (code, message) if the response is a CHPP error envelope."""
    code = _i(root, "ErrorCode")
    if code is None and (_t(root, "FileName", "") or "").lower().startswith("chpperror"):
        code = -1
    if code is None:
        return None
    return code, _t(root, "Error", "")


def parse_teamdetails(xml: str) -> dict:
    root = ET.fromstring(xml)
    user_el = root.find("User")
    user = {
        "ht_user_id": _i(user_el, "UserID") if user_el is not None else _i(root, "UserID"),
        "login_name": _t(user_el, "Loginname") if user_el is not None else None,
        "last_login": _dt(user_el, "LastLoginDate") if user_el is not None else None,
        "supporter_tier": _t(user_el, "SupporterTier") if user_el is not None else None,
    }
    nt_staff = []
    for nt in root.iter("NationalTeam"):
        staff_type = _i(nt, "NationalTeamStaffType")
        if staff_type is not None:
            nt_staff.append({
                "staff_type": staff_type,
                "national_team_id": _i(nt, "NationalTeamID"),
                "national_team_name": _t(nt, "NationalTeamName"),
            })
    teams = []
    teams_el = root.find("Teams")
    team_els = teams_el.findall("Team") if teams_el is not None else root.findall("Team")
    for tm in team_els:
        teams.append({
            "team_id": _i(tm, "TeamID"),
            "team_name": _t(tm, "TeamName", ""),
            "is_primary": _b(tm, "IsPrimaryClub", True),
            "is_bot": _b(tm, "BotStatus/IsBot"),
            "league_id": _i(tm, "League/LeagueID"),
            "league_name": _t(tm, "League/LeagueName", ""),
        })
    return {"user": user, "teams": teams, "nt_staff": nt_staff}


def parse_players(xml: str) -> list[dict]:
    root = ET.fromstring(xml)
    team = root.find("Team")
    if team is None:
        return []
    player_list = team.find("PlayerList")
    if player_list is None:
        return []
    players = []
    for p in player_list.findall("Player"):
        skills = {}
        for key, tag in SKILL_TAGS.items():
            v = _i(p, tag)
            if v is not None:
                skills[key] = v
        players.append({
            "ht_player_id": _i(p, "PlayerID"),
            "first_name": _t(p, "FirstName", ""),
            "last_name": _t(p, "LastName", ""),
            "age_years": _i(p, "Age"),
            "age_days": _i(p, "AgeDays"),
            "tsi": _i(p, "TSI"),
            "salary": _i(p, "Salary"),
            "specialty_id": _i(p, "Specialty", 0),
            "skills": skills or None,
            # TrainerData is present only on the team's coach. Two scales:
            # TrainerSkillLevel is the modern 1–5 coach scale (default view);
            # TrainerSkill is the old denominated value (viewOldCoaches only).
            "trainer_skill": _i(p, "TrainerData/TrainerSkill"),
            "trainer_skill_level": _i(p, "TrainerData/TrainerSkillLevel"),
        })
    return players


def parse_training(xml: str) -> dict:
    root = ET.fromstring(xml)
    team = root.find("Team")
    base = team if team is not None else root
    return {
        "training_type_id": _i(base, "TrainingType"),
        "training_level": _i(base, "TrainingLevel"),
        "stamina_part": _i(base, "StaminaTrainingPart"),
        "coach_level": _first_int(
            base,
            "Trainer/TrainerSkillLevel",
            "Trainer/TrainerSkill",
            "Trainer/TrainerLevel",
            "TrainerLevel",
        ),
        "assistant_level": _first_int(
            base, "AssistantTrainersLevel", "AssistantTrainerLevels"
        ),
    }


def parse_economy(xml: str) -> dict:
    root = ET.fromstring(xml)
    team = root.find("Team")
    base = team if team is not None else root
    return {
        "cash": _i(base, "Cash"),
        "expected_cash": _i(base, "ExpectedCash"),
    }


def parse_playerdetails(xml: str) -> dict:
    root = ET.fromstring(xml)
    p = root.find("Player")
    if p is None:
        raise ValueError("playerdetails response has no Player element")
    return {
        "ht_player_id": _i(p, "PlayerID"),
        "first_name": _t(p, "FirstName", ""),
        "last_name": _t(p, "LastName", ""),
        "age_years": _i(p, "Age"),
        "age_days": _i(p, "AgeDays"),
        "tsi": _i(p, "TSI"),
        "salary": _i(p, "Salary"),
        "specialty_id": _i(p, "Specialty", 0),
        "caps": _i(p, "Caps"),
        "caps_u20": _i(p, "CapsU20"),
        "owner_team_id": _i(p, "OwningTeam/TeamID"),
        "owner_team_name": _t(p, "OwningTeam/TeamName"),
        "owner_league_id": _i(p, "OwningTeam/LeagueID"),
        # Non-zero when the player is part of a national team. Whether the
        # NT prospect list counts as "part of" is undocumented — verify
        # empirically with a prospect who is not in the actual squad.
        "national_team_id": _i(p, "NationalTeamID"),
        "national_team_name": _t(p, "NationalTeamName"),
        "transfer_listed": _b(p, "TransferListed"),
        "asking_price": _i(p, "TransferDetails/AskingPrice"),
        "deadline": _dt(p, "TransferDetails/Deadline"),
        "highest_bid": _i(p, "TransferDetails/HighestBid"),
    }


def _rate(raw: str | None):
    """CurrencyRate arrives with a comma decimal separator (e.g. '5,1129')."""
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def parse_worlddetails(xml: str, league_id: int) -> dict | None:
    """Return {currency_name, currency_rate} for one league, or None.

    CHPP money values are SEK: local amount = value / currency_rate.
    """
    root = ET.fromstring(xml)
    for league in root.iter("League"):
        if _i(league, "LeagueID") != league_id:
            continue
        country = league.find("Country")
        base = country if country is not None else league
        return {
            "currency_name": _t(base, "CurrencyName"),
            "currency_rate": _rate(_t(base, "CurrencyRate")),
        }
    return None
