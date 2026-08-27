"""Demo data for mock mode. Mirrors the CHPP fixtures in app/chpp/fixtures so
that a mock re-sync reproduces the same facts."""
from __future__ import annotations

from datetime import datetime, timedelta

from . import models
from .db import SessionLocal


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(models.User).first() is not None:
            return
        now = datetime.utcnow()

        def user(ht_id, name, role):
            u = models.User(ht_user_id=ht_id, login_name=name, role=role)
            db.add(u)
            return u

        head = user(101, "GenchoHC", models.ROLE_HEAD_COACH)
        user(102, "AsenAC", models.ROLE_ASSISTANT_COACH)
        master = user(103, "MitkoMaster", models.ROLE_MASTER_SCOUT)
        scout1 = user(104, "SashoScout", models.ROLE_POSITION_SCOUT)
        scout2 = user(105, "PepiScout", models.ROLE_POSITION_SCOUT)
        tr1 = user(201, "BorkoTrainer", models.ROLE_TRAINER)
        tr2 = user(202, "ZharkoTrainer", models.ROLE_TRAINER)
        tr3 = user(203, "TishoTrainer", models.ROLE_TRAINER)
        tr4 = user(204, "GhostManager", models.ROLE_TRAINER)
        db.flush()

        p1 = models.TrainerProfile(
            user_id=tr1.id, team_id=1001, team_name="FC Vitosha 09",
            training_type="playmaking", training_intensity=100, stamina_share=10,
            coach_level=7, assistant_level=10,
            cash=9_800_000, expected_cash=12_400_000,
            ht_last_login=now - timedelta(days=1), last_sync=now,
        )
        p2 = models.TrainerProfile(
            user_id=tr2.id, team_id=1002, team_name="Cherno More Youth",
            training_type="winger", training_intensity=95, stamina_share=15,
            coach_level=6, assistant_level=8,
            cash=1_400_000, expected_cash=3_400_000,
            ht_last_login=now - timedelta(days=5), last_sync=now,
        )
        p3 = models.TrainerProfile(
            user_id=tr3.id, team_id=1003, team_name="Ludogorets Fan Club",
            training_type="scoring", training_intensity=90, stamina_share=20,
            coach_level=5, assistant_level=5,
            cash=750_000, expected_cash=800_000,
            ht_last_login=now - timedelta(days=19), last_sync=now,
        )
        p4 = models.TrainerProfile(
            user_id=tr4.id, team_id=1004, team_name="Abandoned FC",
            training_type="defending", coach_level=4,
            cash=5_000_000, expected_cash=5_000_000, is_bot=True,
            ht_last_login=now - timedelta(days=200), last_sync=now,
        )
        db.add_all([p1, p2, p3, p4])
        db.flush()

        def squad(profile, ht_id, name, years, days, spec, tsi, salary, skills, trained):
            db.add(models.SquadPlayer(
                profile_id=profile.id, ht_player_id=ht_id, name=name,
                age_years=years, age_days=days, specialty_id=spec,
                tsi=tsi, salary=salary, skills=skills, in_trained_position=trained,
            ))

        squad(p1, 60011, "Stanislav Mladenov", 17, 44, 1, 10980, 4300,
              {"stamina": 6, "playmaking": 7, "passing": 5, "defending": 4}, True)
        squad(p1, 60012, "Kaloyan Radev", 18, 12, 0, 15400, 6100,
              {"stamina": 7, "playmaking": 8, "passing": 6, "defending": 5}, True)
        squad(p1, 60013, "Veselin Donchev", 24, 80, 3, 8200, 5200,
              {"stamina": 8, "defending": 7, "playmaking": 5}, False)
        squad(p1, 60014, "Dimo Karadzhov", 29, 5, 5, 3900, 3400,
              {"stamina": 7, "goalkeeping": 7, "set_pieces": 6}, False)

        squad(p2, 60021, "Ivan Petkov", 18, 96, 2, 13100, 5600,
              {"stamina": 6, "winger": 7, "playmaking": 4}, True)
        squad(p2, 60022, "Rosen Apostolov", 17, 20, 2, 9800, 4100,
              {"stamina": 5, "winger": 6, "playmaking": 3}, True)
        squad(p2, 60023, "Hristo Bonev", 27, 50, 0, 4300, 3000,
              {"stamina": 7, "defending": 6}, False)

        squad(p3, 60031, "Yordan Minchev", 17, 70, 3, 11200, 4700,
              {"stamina": 6, "scoring": 7, "passing": 4}, True)
        squad(p3, 60032, "Plamen Getov", 25, 30, 0, 5100, 3600,
              {"stamina": 7, "scoring": 5, "defending": 5}, False)

        d1 = models.Declaration(
            profile_id=p1.id, slot_type="playmaking", quality_threshold=7,
            timing="immediate", note="Room for one more 17yo in the rotation.",
            valid_until=now + timedelta(days=21),
        )
        d2 = models.Declaration(
            profile_id=p2.id, slot_type="winger", quality_threshold=6,
            player_to_move="Ivan Petkov (18.96)", expected_sale_price=2_000_000,
            timing="after_cycle", conditional_on_sale=True,
            note="Will free the slot once Petkov sells.",
            valid_until=now + timedelta(days=10),
        )
        d3 = models.Declaration(
            profile_id=p3.id, slot_type="scoring", quality_threshold=6,
            timing="immediate", note="Old declaration, never renewed.",
            valid_until=now - timedelta(days=3),
        )
        db.add_all([d1, d2, d3])

        pl1 = models.TrackedPlayer(
            ht_player_id=5001, name="Georgi Kolev", squad="u21",
            target_skill="playmaking", estimated_price=2_800_000,
            market_status="planned", expected_listing=now + timedelta(days=5),
            notes="Talked to the owner — will list after the cup match.",
            added_by_id=scout1.id,
            age_years=17, age_days=32, tsi=12400, salary=4900, specialty_id=1,
            owner_team_id=2101, owner_team_name="Botev Youth Academy",
            caps=0, caps_u20=3, last_public_sync=now,
        )
        pl2 = models.TrackedPlayer(
            ht_player_id=5002, name="Martin Panayotov", squad="u21",
            target_skill="winger", estimated_price=1_200_000,
            market_status="watching",
            notes="Promising, owner not selling yet.",
            added_by_id=scout1.id,
            age_years=16, age_days=90, tsi=8600, salary=3800, specialty_id=2,
            owner_team_id=2102, owner_team_name="Spartak Varna 22",
            caps=0, caps_u20=0, last_public_sync=now,
        )
        pl3 = models.TrackedPlayer(
            ht_player_id=5003, name="Petar Ivanov", squad="senior",
            target_skill="scoring", estimated_price=3_500_000,
            market_status="listed",
            notes="On the market NOW — deadline in two days.",
            added_by_id=scout2.id,
            age_years=18, age_days=10, tsi=16900, salary=6600, specialty_id=4,
            owner_team_id=2103, owner_team_name="Etar 1924",
            asking_price=3_200_000, deadline=now + timedelta(days=2),
            caps=1, caps_u20=5, last_public_sync=now,
        )
        db.add_all([pl1, pl2, pl3])
        db.flush()

        db.add(models.Claim(player_id=pl1.id, scout_id=scout1.id))
        db.add(models.Claim(player_id=pl3.id, scout_id=scout2.id))
        db.add(models.Interest(
            player_id=pl1.id, profile_id=p1.id,
            note="Fits my playmaking rotation, budget is there.",
        ))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    from .db import init_db

    init_db()
    seed_if_empty()
    print("Seeded (if the database was empty).")
