from datetime import datetime
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "app" / "chpp" / "fixtures"

from app.chpp import parse  # noqa: E402
from app.chpp.client import MockCHPPClient  # noqa: E402
from app.chpp.errors import CHPPError, NotAuthorizedByOwner, error_for_code  # noqa: E402


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_teamdetails():
    data = parse.parse_teamdetails(read("teamdetails_201.xml"))
    assert data["user"]["ht_user_id"] == 201
    assert data["user"]["login_name"] == "BorkoTrainer"
    assert isinstance(data["user"]["last_login"], datetime)
    assert data["teams"][0]["team_id"] == 1001
    assert data["teams"][0]["is_bot"] is False
    assert data["nt_staff"] == []


def test_parse_players_own_team_has_skills():
    players = parse.parse_players(read("players_1001.xml"))
    assert len(players) == 4
    stan = players[0]
    assert stan["ht_player_id"] == 60011
    assert stan["skills"]["playmaking"] == 7
    assert stan["age_years"] == 17 and stan["age_days"] == 44


def test_parse_training_and_economy():
    tr = parse.parse_training(read("training_1001.xml"))
    assert tr["training_type_id"] == 8  # 8 = Playmaking (0-based CHPP scheme)
    assert tr["coach_level"] == 7
    ec = parse.parse_economy(read("economy_1001.xml"))
    assert ec["cash"] == 9_800_000
    assert ec["expected_cash"] == 12_400_000


def test_parse_playerdetails_listed():
    d = parse.parse_playerdetails(read("playerdetails_5003.xml"))
    assert d["transfer_listed"] is True
    assert d["asking_price"] == 3_200_000
    assert d["deadline"].year == 2026
    assert d["owner_team_name"] == "Etar 1924"
    assert d["national_team_id"] == 3175
    assert d["national_team_name"] == "Bulgaria"


def test_parse_playerdetails_not_listed():
    d = parse.parse_playerdetails(read("playerdetails_5001.xml"))
    assert d["transfer_listed"] is False
    assert d["asking_price"] is None
    assert d["caps_u20"] == 3


def test_error_envelope_raises_59():
    import xml.etree.ElementTree as ET

    root = ET.fromstring(read("chpperror.xml"))
    code, msg = parse.parse_error(root)
    assert code == 59
    assert isinstance(error_for_code(code, msg), NotAuthorizedByOwner)


def test_parse_worlddetails_and_comma_rate():
    xml = read("worlddetails.xml")
    mock = parse.parse_worlddetails(xml, 50)
    assert mock == {"currency_name": "€", "currency_rate": 1.0}
    comma = parse.parse_worlddetails(xml, 51)
    assert comma["currency_rate"] == 5.1129  # '5,1129' with comma separator
    assert parse.parse_worlddetails(xml, 999) is None


def test_parse_players_trainer_data():
    players = parse.parse_players(read("players_1001.xml"))
    coach = next(p for p in players if p["ht_player_id"] == 60014)
    assert coach["trainer_skill"] == 7
    outfield = next(p for p in players if p["ht_player_id"] == 60011)
    assert outfield["trainer_skill"] is None
    assert outfield["trainer_skill_level"] is None


def test_coach_level_scales():
    from app.services.sync import coach_level_from_squad

    # Old denominated TrainerSkill (viewOldCoaches) is used verbatim.
    assert coach_level_from_squad([{"trainer_skill": 7}]) == 7
    # Modern 1–5 TrainerSkillLevel maps to denominations 4–8:
    # 4/5 coach = solid (7), 5/5 = excellent (8), 1/5 = weak (4).
    assert coach_level_from_squad([{"trainer_skill_level": 4}]) == 7
    assert coach_level_from_squad([{"trainer_skill_level": 5}]) == 8
    assert coach_level_from_squad([{"trainer_skill_level": 1}]) == 4
    # No coach in the squad list.
    assert coach_level_from_squad([{"trainer_skill": None}]) is None


def test_training_type_mapping_is_zero_based():
    # Verified against lucianoq/hattrick and live data: user training
    # "Short passes" arrives as TrainingType 7.
    from app.chpp.constants import TRAINING_TYPE_TO_SKILL as M

    assert M[7] == "passing"
    assert M[8] == "playmaking"
    assert M[9] == "goalkeeping"
    assert M[4] == "scoring"
    assert M[5] == "winger"
    assert 0 not in M and 1 not in M  # deprecated types fall back to "other"


def test_mock_client_resolves_by_id_and_missing_raises():
    c = MockCHPPClient()
    xml = c.fetch("playerdetails", "3.2", playerID=5001)
    assert "Georgi" in xml
    with pytest.raises(CHPPError):
        c.fetch("playerdetails", "3.2", playerID=999999)
