"""End-to-end walk through the core product flows against the seeded mock DB."""
from conftest import login


def test_login_page_lists_personas(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "SashoScout" in r.text
    assert "BorkoTrainer" in r.text


def test_scout_flow(client):
    login(client, 104)  # position scout

    # Dashboard renders with the seeded open interest from BorkoTrainer.
    r = client.get("/")
    assert r.status_code == 200
    assert "FC Vitosha 09" in r.text

    # Registry shows seeded players.
    r = client.get("/players")
    assert "Georgi Kolev" in r.text
    assert "Petar Ivanov" in r.text

    # Capacity registry: bot hidden by default, bands visible, exact cash not.
    r = client.get("/trainers")
    assert "FC Vitosha 09" in r.text
    assert "Abandoned FC" not in r.text
    assert "12 400 000" not in r.text  # position scout sees bands only
    r2 = client.get("/trainers", params={"include_stale": "1"})
    assert "Abandoned FC" in r2.text

    # Budget filter: ≥ 5M keeps only Vitosha (12.4M expected).
    r3 = client.get("/trainers", params={"min_budget": "5000000"})
    assert "FC Vitosha 09" in r3.text
    assert "Cherno More Youth" not in r3.text  # 3.4M
    assert "Ludogorets Fan Club" not in r3.text  # 0.8M
    # A bogus threshold value is ignored, not an error.
    r4 = client.get("/trainers", params={"min_budget": "123"})
    assert "Cherno More Youth" in r4.text

    # Declaration filters: slot for playmaking → only Vitosha declared one;
    # Ludogorets' scoring declaration is expired so it never matches.
    r5 = client.get("/trainers", params={"slot_skill": "playmaking"})
    assert "FC Vitosha 09" in r5.text
    assert "Cherno More Youth" not in r5.text
    assert "Ludogorets Fan Club" not in r5.text
    # Timing filter: after_cycle → only the winger slot.
    r6 = client.get("/trainers", params={"slot_timing": "after_cycle"})
    assert "Cherno More Youth" in r6.text
    assert "FC Vitosha 09" not in r6.text
    # The declaration requirements are visible in the slots column.
    assert "1 500 000" in r6.text  # trainer's max price
    assert "Winger ≥ 6" in r6.text  # skill requirement
    assert "…–18" in r6.text  # max age requirement

    # Add a new player -> public data auto-fills from the mock fixture.
    r = client.post("/players/new", data={
        "ht_player_id": "5004",
        "squad": "u21",
        "plan_skill_1": "goalkeeping",
        "plan_weeks_1": "40",
        "plan_skill_2": "set_pieces",
        "plan_weeks_2": "10",
        "estimated_price": "900000",
        "market_status": "watching",
        "expected_listing": "",
        "notes": "keeper prospect",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "Stefan Bozhkov" in r.text  # name came from playerdetails_5004.xml
    assert "Slavia Sofia Reserves" in r.text

    # Player detail for a claimed player shows matching trainers with reasons.
    r = client.get("/players")
    assert "Stefan Bozhkov" in r.text


def test_player_detail_matching_and_no_raw_keys(client):
    login(client, 101)  # head coach sees exact figures
    r = client.get("/players/1")  # Georgi Kolev (playmaking)
    assert r.status_code == 200
    assert "FC Vitosha 09" in r.text
    assert "12 400 000" in r.text  # exact finance for head coach
    assert "newMail" in r.text  # compose link present
    assert 'class="draft-subject"' in r.text  # prefilled subject to copy
    assert "copy-btn" in r.text  # one-click copy for subject/message
    for fragment in ("reason_", "warn_", "band_", "skill_", "fl_"):
        assert fragment not in r.text, f"unresolved i18n key: {fragment}"


def test_trainer_flow(client):
    login(client, 202)  # ZharkoTrainer (winger)

    # Market pipeline shows planned/listed players, not the watched one.
    r = client.get("/market")
    assert "Georgi Kolev" in r.text
    assert "Petar Ivanov" in r.text
    assert "Martin Panayotov" not in r.text

    # Express interest in the listed scorer.
    r = client.get("/players")  # trainers have no access to the scout registry
    assert r.history and r.history[0].status_code == 303

    r = client.post("/players/3/interest", data={
        "note": "have cash now", "max_bid": "3 600 000",
    }, follow_redirects=True)
    assert r.status_code == 200

    # Declaration lifecycle: create with horizon, max price and requirements.
    r = client.post("/declarations", data={
        "slot_type": "winger",
        "training_weeks": "50",
        "timing": "immediate",
        "max_price": "2 200 000",
        "min_age": "16",
        "max_age": "19",
        "specialty": "2",
        "req_min_winger": "6",
        "req_max_stamina": "9",
        "note": "second slot",
        "valid_days": "28",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "second slot" in r.text
    assert "2 200 000" in r.text          # max price shown
    assert "16–19" in r.text              # age requirement
    assert "Winger ≥ 6" in r.text         # skill requirement
    assert "Stamina ≤ 9" in r.text


def test_training_plan_and_skills(client):
    login(client, 101)  # head coach (scout permissions)

    # Scout enters current skills + age via the assessment form.
    r = client.post("/players/1/status", data={
        "market_status": "planned",
        "estimated_price": "2800000",
        "expected_listing": "",
        "notes": "Talked to the owner — will list after the cup match.",
        "age_years": "17", "age_days": "32", "specialty": "1",
        "sk_playmaking": "7", "sk_passing": "5", "sk_stamina": "6",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "solid (7)" in r.text  # playmaking chip, denominated

    # Two plan steps: playmaking first, then passing.
    r = client.post("/players/1/plan", data={
        "skill": "playmaking", "weeks": "16", "stamina_share": "10",
    }, follow_redirects=True)
    r = client.post("/players/1/plan", data={
        "skill": "passing", "weeks": "8", "stamina_share": "15",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "16" in r.text and "Passing" in r.text

    # The plan lands in the outreach draft.
    assert "Suggested training plan" in r.text
    assert "Playmaking ~16 wk (10% stamina)" in r.text

    # Trainers see the plan and skills in the market pipeline.
    login(client, 201)
    r = client.get("/market")
    assert "~16 wk" in r.text
    assert "Playmaking 7" in r.text

    # Scout can remove a step.
    login(client, 101)
    r = client.get("/players/1")
    import re

    sid = re.search(r"/plan/(\d+)/delete", r.text).group(1)
    r = client.post(f"/plan/{sid}/delete", follow_redirects=True)
    assert r.status_code == 200


def test_scout_accepts_interest(client):
    login(client, 105)  # PepiScout claims player 3 in seed
    r = client.get("/players/3")
    assert "have cash now" in r.text
    assert "3 600 000" in r.text  # the trainer's declared bid limit
    # Find the interest id via the decision form action.
    import re

    m = re.search(r"/interests/(\d+)/decision", r.text)
    assert m
    iid = m.group(1)
    r = client.post(f"/interests/{iid}/decision", data={"action": "accept"}, follow_redirects=True)
    assert r.status_code == 200
    assert "Cherno More Youth" in r.text  # claim now linked to the trainer


def test_admin_role_change(client):
    login(client, 101)
    r = client.get("/admin")
    assert r.status_code == 200
    r = client.post("/admin/roles", data={"user_id": "5", "role": "master_scout"}, follow_redirects=True)
    assert r.status_code == 200

    # A master scout can also manage roles…
    login(client, 103)
    r = client.get("/admin")
    assert r.status_code == 200
    r = client.post("/admin/roles", data={"user_id": "9", "role": "position_scout"}, follow_redirects=True)
    assert "Role updated" in r.text

    # …but cannot grant or touch the head-coach role.
    r = client.post("/admin/roles", data={"user_id": "3", "role": "head_coach"}, follow_redirects=True)
    assert "access" in r.text  # denied flash
    r = client.post("/admin/roles", data={"user_id": "1", "role": "trainer"}, follow_redirects=True)
    assert "access" in r.text  # cannot demote the head coach

    # Pre-provision a user by Hattrick ID: they appear with the given role
    # and keep it on first login.
    login(client, 101)
    r = client.post("/admin/users", data={
        "ht_user_id": "300", "login_name": "NewScout", "role": "position_scout",
    }, follow_redirects=True)
    assert "NewScout" in r.text
    r = client.post("/admin/users", data={
        "ht_user_id": "300", "login_name": "Dup", "role": "trainer",
    }, follow_redirects=True)
    assert "already exists" in r.text
    # Master scout cannot pre-provision a head coach.
    login(client, 103)
    r = client.post("/admin/users", data={
        "ht_user_id": "301", "login_name": "Sneaky", "role": "head_coach",
    }, follow_redirects=True)
    assert "access" in r.text

    # Plain trainers get bounced.
    login(client, 202)
    r = client.get("/admin")
    assert r.history and r.history[0].status_code == 303


def test_sync_throttle_and_owner_force(client):
    # Scout-side player refresh honours the 24h fetch policy.
    login(client, 104)
    r = client.post("/players/1/sync", follow_redirects=True)
    assert "Public data refreshed" in r.text
    r = client.post("/players/1/sync", follow_redirects=True)
    assert "24h" in r.text  # throttled

    # Owner-initiated team refresh is manual → always allowed.
    login(client, 201)
    r = client.post("/me/sync", follow_redirects=True)
    assert "refreshed from CHPP" in r.text
    r = client.post("/me/sync", follow_redirects=True)
    assert "refreshed from CHPP" in r.text
    # Mock worlddetails has rate 1 / € — currency shows, values unchanged.
    assert "9 800 000 €" in r.text
    # Coach level from stafflist (4/5 → solid) and the specialists list.
    assert "solid" in r.text
    assert "Assistant coach 5" in r.text
    assert "Form coach 4" in r.text


def test_comments_replies_and_mail_modal(client):
    # A trainer starts the discussion under Georgi Kolev.
    login(client, 202)
    r = client.post("/players/1/comments", data={
        "body": "Would he accept a mid-week friendly schedule?",
    }, follow_redirects=True)
    assert "mid-week friendly" in r.text
    # Trainers get no HT-mail modal.
    assert "mail-c" not in r.text

    # A scout replies and sees the mail modal with the [playerid=…] code.
    login(client, 104)
    r = client.get("/players/1")
    import re

    cid = re.search(r'name="parent_id" value="(\d+)"', r.text).group(1)
    r = client.post("/players/1/comments", data={
        "body": "Yes, owner confirmed.", "parent_id": cid,
    }, follow_redirects=True)
    assert "Yes, owner confirmed." in r.text
    # The mail button shows on every comment for non-trainer roles,
    # the scout's own reply included.
    assert r.text.count('class="mail-modal"') == 2
    assert "[playerid=5001]" in r.text  # HT message markup in the draft
    assert "Would he accept a mid-week friendly schedule?" in r.text  # quote
    assert 'class="mail-modal"' in r.text

    # The trainer cannot delete the scout's reply; the author can delete
    # their own comment (cascading the reply).
    login(client, 202)
    r = client.get("/players/1")
    m = re.search(r"/comments/(\d+)/delete", r.text)
    assert m  # own comment is deletable
    r = client.post(f"/comments/{m.group(1)}/delete", follow_redirects=True)
    assert "mid-week friendly" not in r.text
    assert "Yes, owner confirmed." not in r.text  # reply went with it


def test_row_actions_quickstatus_and_delete(client):
    # A position scout cannot delete a player someone else added.
    login(client, 104)
    r = client.post("/players/3/delete", follow_redirects=True)  # added by 105
    assert "Petar Ivanov" in r.text  # still there

    login(client, 101)  # head coach is privileged
    # Quick status: mark the listed scorer as sold — his claim completes.
    r = client.post("/players/3/quickstatus", data={"market_status": "transferred"}, follow_redirects=True)
    assert r.status_code == 200
    r = client.get("/players/3")
    assert "unclaimed" in r.text  # active claim was auto-completed

    # Delete the keeper prospect added earlier in the scout flow.
    r = client.post("/players/4/delete", follow_redirects=True)
    assert r.status_code == 200
    assert "Stefan Bozhkov" not in r.text


def test_multi_team_choice(client):
    # SashoScout manages two teams (mock fixture) and has no profile yet:
    # connecting must ask which team, never guess.
    login(client, 104)
    r = client.post("/me/sync", follow_redirects=True)
    assert "Sasho United" in r.text and "Sasho Ladies" in r.text
    assert "Choose" in r.text  # landed on the team chooser

    # Pick the NON-primary team — proves the choice is honoured.
    r = client.post("/me/team", data={"team_id": "1042"}, follow_redirects=True)
    assert "Sasho Ladies" in r.text
    assert "Defending" in r.text  # training type of team 1042
    assert "2 400 000" in r.text  # its expected cash

    # A team that is not theirs is rejected.
    r = client.post("/me/team", data={"team_id": "9999"}, follow_redirects=True)
    assert "does not belong" in r.text

    # The chooser marks the connected team and offers the other one.
    r = client.get("/me/teams")
    assert "Connected" in r.text
    assert "Sasho United" in r.text

    # Dual role: a scout with a connected team sees BOTH the scout sections
    # and the trainer-interest form (with the bid limit) on a player page.
    r = client.get("/players/1")
    assert "Matching trainers" in r.text
    assert "I want to train him" in r.text
    assert 'name="max_bid"' in r.text


def test_cron_sync_batches_and_throttles(client):
    # In mock mode with no CRON_SECRET the endpoint is open (dev only).
    r = client.get("/cron/sync")
    assert r.status_code == 200
    data = r.json()
    # 202/203 were never synced during the suite → refreshed now; teams
    # synced earlier in the run are inside the 24h window → skipped.
    assert data["trainers_ok"] >= 1
    assert data["trainers_skipped"] >= 1
    assert data["players_ok"] >= 1

    # A second run finds everything freshly synced.
    r2 = client.get("/cron/sync")
    d2 = r2.json()
    assert d2["trainers_ok"] == 0
    assert d2["players_ok"] == 0
    assert d2["trainers_skipped"] >= 2


def test_declaration_renew_and_market_visibility(client):
    login(client, 203)  # TishoTrainer has an expired declaration
    r = client.get("/me")
    assert r.status_code == 200
    import re

    m = re.search(r"/declarations/(\d+)/renew", r.text)
    assert m
    r = client.post(f"/declarations/{m.group(1)}/renew", follow_redirects=True)
    assert r.status_code == 200
