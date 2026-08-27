"""Targeted outreach: prefilled HT-mail compose links and message drafts.

Sending is ALWAYS manual, one message at a time, in the Hattrick UI — there is
no messaging API and bulk messaging is a game-rules violation. This module
only produces a URL and text for the scout to copy.
"""
from __future__ import annotations

from .. import models
from ..i18n import t


def compose_url(ht_user_id: int) -> str:
    return f"https://www.hattrick.org/MyHattrick/Inbox/?actionType=newMail&userid={ht_user_id}"


def player_url(ht_player_id: int) -> str:
    return f"https://www.hattrick.org/Club/Players/Player.aspx?playerId={ht_player_id}"


def _fmt_money(v) -> str:
    return f"{v:,}".replace(",", " ") if v is not None else "?"


def comment_mail_body(locale: str, player: models.TrackedPlayer, comment) -> str:
    """HT-mail draft about a specific comment. Uses Hattrick's message markup
    [playerid=NNN], which renders as a player link inside HT-mail."""
    return t(
        locale,
        "comment_mail_body",
        author=comment.author.login_name,
        playerid=player.ht_player_id,
        quote=comment.body,
    )


def draft_subject(locale: str, player: models.TrackedPlayer) -> str:
    return t(
        locale,
        "outreach_subject",
        player=player.name or f"#{player.ht_player_id}",
        skill=t(locale, f"skill_{player.target_skill}"),
    )


def plan_text(locale: str, player: models.TrackedPlayer) -> str:
    steps = [
        t(
            locale,
            "plan_step_fmt",
            skill=t(locale, f"skill_{s.skill}"),
            weeks=s.weeks if s.weeks is not None else "?",
            stamina=s.stamina_share if s.stamina_share is not None else "?",
        )
        for s in player.plan_steps
    ]
    return " → ".join(steps)


def draft_message(locale: str, player: models.TrackedPlayer, trainer_user: models.User, scout: models.User) -> str:
    price_part = ""
    if player.estimated_price:
        price_part = t(locale, "draft_price_part", price=_fmt_money(player.estimated_price))
    plan_part = ""
    if player.plan_steps:
        plan_part = t(locale, "draft_plan_part", plan=plan_text(locale, player))
    age = f"{player.age_years}.{player.age_days}" if player.age_years is not None else "?"
    return t(
        locale,
        "outreach_draft",
        trainer=trainer_user.login_name,
        scout=scout.login_name,
        squad=t(locale, f"squad_{player.squad}"),
        player=player.name or f"#{player.ht_player_id}",
        age=age,
        skill=t(locale, f"skill_{player.target_skill}"),
        price_part=price_part,
        plan_part=plan_part,
        url=player_url(player.ht_player_id),
    )
