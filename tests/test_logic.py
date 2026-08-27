from datetime import datetime, timedelta

from app import models
from app.services.capacity import budget_band, covers
from app.services.matching import declaration_active, rank_trainers, renew

NOW = datetime(2026, 8, 3, 12, 0, 0)


def profile(**kw):
    defaults = dict(
        team_id=1, team_name="T", training_type="playmaking",
        cash=1_000_000, expected_cash=2_000_000,
        is_bot=False, ht_last_login=NOW - timedelta(days=1), coach_level=6,
    )
    defaults.update(kw)
    return models.TrainerProfile(**defaults)


def decl(**kw):
    defaults = dict(
        slot_type="playmaking", timing="immediate",
        status="active", valid_until=NOW + timedelta(days=10),
    )
    defaults.update(kw)
    return models.Declaration(**defaults)


def player(**kw):
    defaults = dict(ht_player_id=1, target_skill="playmaking", estimated_price=1_500_000)
    defaults.update(kw)
    return models.TrackedPlayer(**defaults)


def user(name="u"):
    return models.User(ht_user_id=1, login_name=name)


def test_u21_until():
    from app.util import u21_until

    # 17y 32d at the snapshot: 22*112 - (17*112 + 32) = 528 days remain.
    until = u21_until(17, 32, NOW)
    assert (until - NOW).days == 528
    # 21y 111d: one day before the 22nd birthday.
    assert (u21_until(21, 111, NOW) - NOW).days == 1
    # Already 22 → the date lies in the past.
    assert u21_until(22, 4, NOW) < NOW
    assert u21_until(None, 30, NOW) is None
    assert u21_until(17, 32, None) is None


def test_last_u21_match():
    from datetime import datetime

    from app.util import last_u21_match

    # The user's real example: eligibility ends 2027-09-12 → the last playable
    # match is World Cup Round 4 #1 on 2027-09-10 (the 09-13 match is too late).
    date, label = last_u21_match(datetime(2027, 9, 12))
    assert date == "2027-09-10"
    assert label == "World Cup Round 4 : #1"

    # Before the first match in the calendar → nothing playable.
    assert last_u21_match(datetime(2026, 8, 1)) is None
    # After the calendar's end → the final of the last edition.
    date, label = last_u21_match(datetime(2030, 1, 1))
    assert date == "2029-08-10"
    assert "Final" in label
    assert last_u21_match(None) is None


def test_budget_bands_edges():
    assert budget_band(None) == "band_unknown"
    assert budget_band(0) == "band_0"
    assert budget_band(499_999) == "band_0"
    assert budget_band(500_000) == "band_1"
    assert budget_band(1_999_999) == "band_1"
    assert budget_band(2_000_000) == "band_2"
    assert budget_band(9_999_999) == "band_3"
    assert budget_band(10_000_000) == "band_4"
    assert budget_band(50_000_000) == "band_4"


def test_covers():
    assert covers(2_000_000, 1_500_000)
    assert not covers(1_000_000, 1_500_000)
    assert not covers(None, 1)
    assert not covers(1, None)


def test_declaration_expiry_and_renew():
    d = decl(valid_until=NOW - timedelta(days=1))
    assert not declaration_active(d, NOW)
    renew(d, NOW)
    assert declaration_active(d, NOW)
    assert d.valid_until == NOW + timedelta(days=models.DEFAULT_DECLARATION_DAYS)
    d.status = "withdrawn"
    assert not declaration_active(d, NOW)


def test_rank_orders_full_match_first_and_skips_bots():
    p = player()
    good = (user("good"), profile(team_name="Good"), [decl()])
    poor = (user("poor"), profile(team_name="Poor", training_type="scoring",
                                  cash=100_000, expected_cash=100_000), [])
    bot = (user("bot"), profile(team_name="Bot", is_bot=True), [decl()])
    results = rank_trainers(p, [poor, bot, good], NOW)
    assert [r.profile.team_name for r in results] == ["Good", "Poor"]
    assert results[0].score > results[1].score
    keys = [k for k, _ in results[0].reasons]
    assert "reason_training_match" in keys
    assert "reason_slot_declared" in keys
    assert "reason_budget_ok" in keys


def test_rank_expired_declaration_does_not_count():
    p = player()
    expired = (user(), profile(), [decl(valid_until=NOW - timedelta(days=1))])
    results = rank_trainers(p, [expired], NOW)
    warn_keys = [k for k, _ in results[0].warnings]
    assert "warn_no_slot" in warn_keys


def test_rank_horizon_warning():
    p = player()
    p.plan_steps = [
        models.TrainingPlanStep(skill="playmaking", weeks=30, position=1),
        models.TrainingPlanStep(skill="passing", weeks=30, position=2),
    ]
    short = (user("short"), profile(), [decl(training_weeks=40)])
    endless = (user("endless"), profile(team_name="U"), [decl()])  # indefinite
    results = rank_trainers(p, [short, endless], NOW)
    by_name = {r.user.login_name: r for r in results}
    assert ("warn_horizon_short", {"declared": 40, "needed": 60}) in by_name["short"].warnings
    assert not any(k == "warn_horizon_short" for k, _ in by_name["endless"].warnings)


def test_rank_declaration_requirements():
    p = player(estimated_price=2_000_000)
    p.age_years = 17
    p.specialty_id = 1  # technical
    p.skills = {"playmaking": 7, "stamina": 6}

    fits = (
        user("fits"),
        profile(team_name="Fits", expected_cash=5_000_000),
        [decl(max_price=2_500_000, min_age=16, max_age=18, specialty_id=1,
              skill_reqs={"playmaking": {"min": 7, "max": None}})],
    )
    picky = (
        user("picky"),
        profile(team_name="Picky", expected_cash=5_000_000),
        [decl(max_price=1_500_000, min_age=18,
              skill_reqs={"playmaking": {"min": 9, "max": None},
                          "stamina": {"min": None, "max": 5}})],
    )
    results = rank_trainers(p, [fits, picky], NOW)
    by_name = {r.user.login_name: r for r in results}

    fit_keys = [k for k, _ in by_name["fits"].reasons]
    assert "reason_requirements_ok" in fit_keys

    picky_warn = [k for k, _ in by_name["picky"].warnings]
    assert "warn_req_age" in picky_warn          # 17 < min 18
    assert "warn_req_skill_low" in picky_warn    # playmaking 7 < 9
    assert "warn_req_skill_high" in picky_warn   # stamina 6 > max 5
    assert "warn_req_price" in picky_warn        # 2M > max 1.5M
    assert by_name["fits"].score > by_name["picky"].score


def test_rank_requirements_unknown_data_is_not_violation():
    p = player(estimated_price=None)  # nothing known about the player
    bundle = (
        user(),
        profile(),
        [decl(max_price=1_000_000, min_age=18, specialty_id=3,
              skill_reqs={"playmaking": {"min": 9, "max": None}})],
    )
    results = rank_trainers(p, [bundle], NOW)
    warn_keys = [k for k, _ in results[0].warnings]
    assert not any(k.startswith("warn_req_") for k in warn_keys)
