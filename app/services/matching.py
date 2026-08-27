"""Rank trainers against a tracked player — the core scout query.

Pure logic, no DB access: takes (user, profile, declarations) bundles and a
player, returns scored matches with human-readable reason codes. Reason and
warning entries are (i18n_key, params) pairs resolved at render time.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .. import models


def declaration_active(decl: models.Declaration, now: datetime) -> bool:
    return decl.status == "active" and decl.valid_until is not None and decl.valid_until >= now


def renew(decl: models.Declaration, now: datetime, days: int = models.DEFAULT_DECLARATION_DAYS) -> None:
    decl.valid_until = now + timedelta(days=days)
    decl.renewed_at = now
    decl.status = "active"


@dataclass
class MatchResult:
    user: models.User
    profile: models.TrainerProfile
    score: int = 0
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    active_declarations: list = field(default_factory=list)


def rank_trainers(player: models.TrackedPlayer, bundles, now: datetime) -> list[MatchResult]:
    """bundles: iterable of (user, profile, declarations)."""
    results = []
    for user, profile, declarations in bundles:
        if profile.is_bot:
            continue
        r = MatchResult(user=user, profile=profile)

        if profile.training_type == player.target_skill:
            r.score += 40
            r.reasons.append(("reason_training_match", {}))
        else:
            r.warnings.append(("warn_training_mismatch", {}))

        active = [
            d for d in declarations
            if declaration_active(d, now) and d.slot_type in (player.target_skill, "any")
        ]
        r.active_declarations = active
        if active:
            r.score += 25
            r.reasons.append(("reason_slot_declared", {"n": len(active)}))
            if any(d.timing == "immediate" and not d.conditional_on_sale for d in active):
                r.score += 10
                r.reasons.append(("reason_slot_immediate", {}))
            elif any(d.conditional_on_sale for d in active):
                r.warnings.append(("warn_conditional", {}))
            # Does the trainer's declared training horizon cover the plan?
            plan_weeks = sum(
                s.weeks for s in getattr(player, "plan_steps", []) if s.weeks
            )
            horizons = [d.training_weeks for d in active]
            if plan_weeks and None not in horizons and max(horizons) < plan_weeks:
                r.warnings.append((
                    "warn_horizon_short",
                    {"declared": max(horizons), "needed": plan_weeks},
                ))
        else:
            r.warnings.append(("warn_no_slot", {}))

        cash = profile.expected_cash if profile.expected_cash is not None else profile.cash
        if player.estimated_price:
            if cash is None:
                r.warnings.append(("warn_budget_unknown", {}))
            elif cash >= player.estimated_price:
                r.score += 20
                r.reasons.append(("reason_budget_ok", {}))
            elif any(
                d.expected_sale_price and cash + d.expected_sale_price >= player.estimated_price
                for d in active
            ):
                r.score += 8
                r.reasons.append(("reason_budget_after_sale", {}))
            else:
                r.score -= 15
                r.warnings.append(("warn_budget_short", {}))

        if profile.ht_last_login is not None:
            days = (now - profile.ht_last_login).days
            if days <= 3:
                r.score += 10
                r.reasons.append(("reason_login_recent", {}))
            elif days <= 14:
                r.score += 5
                r.reasons.append(("reason_login_ok", {}))
            elif days > 45:
                r.score -= 20
                r.warnings.append(("warn_login_stale", {"days": days}))

        if profile.coach_level is not None:
            if profile.coach_level >= 7:
                r.score += 6
                r.reasons.append(("reason_top_coach", {}))
            elif profile.coach_level >= 5:
                r.score += 3

        results.append(r)

    results.sort(key=lambda m: (-m.score, m.profile.team_name))
    return results
