"""One-shot CHPP diagnostic: fetch the raw XML files for your own team and
save them under debug_xml/ so parser mismatches can be inspected and fixed.

Usage (real mode, after logging in once via the web app so a token exists):

    .venv/bin/python scripts/chpp_probe.py            # all files
    .venv/bin/python scripts/chpp_probe.py training   # just one

Sequential requests, one run at a time — respect the CHPP fetch policy and
don't put this in a loop or a cron job.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import models  # noqa: E402
from app.chpp import client as chpp_client  # noqa: E402
from app.chpp.parse import parse_teamdetails  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402

VERSIONS = {
    "teamdetails": "3.9",
    "training": "2.2",
    "economy": "1.4",
    "players": "2.8",
    "worlddetails": "1.9",
}


def main() -> None:
    wanted = sys.argv[1:] or list(VERSIONS)
    if settings.chpp_mock:
        sys.exit("CHPP_MOCK=1 — this probe is for real mode; set CHPP_MOCK=0 first.")

    init_db()
    db = SessionLocal()
    token = (
        db.query(models.OAuthToken)
        .filter(models.OAuthToken.revoked_at.is_(None))
        .order_by(models.OAuthToken.created_at.desc())
        .first()
    )
    if token is None:
        sys.exit("No OAuth token in the database — log in via the web app first.")

    chpp = chpp_client.get_client(token.token, token.token_secret)
    out = Path(__file__).resolve().parent.parent / "debug_xml"
    out.mkdir(exist_ok=True)

    td_xml = chpp.fetch("teamdetails", VERSIONS["teamdetails"])
    (out / "teamdetails.xml").write_text(td_xml, encoding="utf-8")
    print("saved teamdetails.xml")
    td = parse_teamdetails(td_xml)
    team_id = td["teams"][0]["team_id"]
    print(f"team: {td['teams'][0]['team_name']} ({team_id})")

    params = {
        "training": {"teamId": team_id},
        "economy": {"teamId": team_id},
        "players": {"teamID": team_id},
        "worlddetails": {},
    }
    for name in wanted:
        if name == "teamdetails" or name not in VERSIONS:
            continue
        xml = chpp.fetch(name, VERSIONS[name], **params[name])
        (out / f"{name}.xml").write_text(xml, encoding="utf-8")
        print(f"saved {name}.xml")

    print(f"\nAll files are in {out}/ — attach the relevant one when reporting "
          "a parser mismatch. They contain your private team data; don't share "
          "them publicly.")


if __name__ == "__main__":
    main()
