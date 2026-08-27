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


def _has_requirements(decl: models.Declaration) -> bool:
    return bool(
        decl.min_age or decl.max_age or decl.specialty_id is not None
        or decl.skill_reqs or decl.max_price
    )


def _requirement_violations(decl: models.Declaration, player: models.TrackedPlayer):
    """Which of the declaration's requirements does the player (as far as we
    know him) break? Unknown player data never counts as a violation."""
    violations = []
    if player.age_years is not None:
        if decl.min_age and player.age_years < decl.min_age:
            violations.append(("warn_req_age", {"limit": decl.min_age}))
        if decl.max_age and player.age_years > decl.max_age:
            violations.append(("warn_req_age_max", {"limit": decl.max_age}))
    if (
        decl.specialty_id is not None
        and player.specialty_id is not None
        and decl.specialty_id != player.specialty_id
    ):
        violations.append(("warn_req_spec", {}))
    for skill, req in (decl.skill_reqs or {}).items():
        have = (player.skills or {}).get(skill)
        if have is None:
            continue
        if req.get("min") and have < req["min"]:
            violations.append(("warn_req_skill_low", {"skill": skill, "limit": req["min"]}))
        if req.get("max") and have > req["max"]:
            violations.append(("warn_req_skill_high", {"skill": skill, "limit": req["max"]}))
    if decl.max_price and player.estimated_price and player.estimated_price > decl.max_price:
        violations.append(("warn_req_price", {"limit": decl.max_price}))
    return violations


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
            if any(d.timing == "immediate" for d in active):
                r.score += 10
                r.reasons.append(("reason_slot_immediate", {}))
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
            # Declared requirements vs what we know about the player: judge
            # against the friendliest declaration (fewest violations).
            best = min(
                (( _requirement_violations(d, player), d) for d in active),
                key=lambda pair: len(pair[0]),
            )
            violations, best_decl = best
            if violations:
                r.warnings.extend(violations)
                r.score -= 6 * len(violations)
            elif _has_requirements(best_decl):
                r.score += 8
                r.reasons.append(("reason_requirements_ok", {}))
        else:
            r.warnings.append(("warn_no_slot", {}))

        cash = profile.expected_cash if profile.expected_cash is not None else profile.cash
        if player.estimated_price:
            if cash is None:
                r.warnings.append(("warn_budget_unknown", {}))
            elif cash >= player.estimated_price:
                r.score += 20
                r.reasons.append(("reason_budget_ok", {}))
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
