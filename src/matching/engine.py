from dataclasses import dataclass

from src.db.models import RuleChange, User

# Tags that each visa category cares about
_VISA_TAG_MAP: dict[str, list[str]] = {
    "H-1B":  ["h1b", "h-1b", "specialty-occupation", "h1b-cap", "h1b-extension",
               "h1b-transfer", "site-visits", "third-party-placement", "prevailing-wage", "lca"],
    "H-4":   ["h4", "h-4", "h4-ead", "h-4-ead"],
    "F-1":   ["f1", "f-1", "opt", "stem-opt", "cpt", "student", "sevp", "sevis"],
    "F-2":   ["f2", "f-2", "student-dependent"],
    "L-1":   ["l1", "l-1", "intracompany", "l1a", "l1b"],
    "O-1":   ["o1", "o-1", "extraordinary-ability"],
    "TN":    ["tn", "nafta", "usmca", "canada", "mexico"],
    "J-1":   ["j1", "j-1", "exchange-visitor", "waiver"],
    "EB-1":  ["eb1", "eb-1", "priority-workers", "extraordinary-ability-immigrant"],
    "EB-2":  ["eb2", "eb-2", "advanced-degree", "niw", "national-interest-waiver"],
    "EB-3":  ["eb3", "eb-3", "skilled-workers"],
}

_GC_STAGE_TAG_MAP: dict[str, list[str]] = {
    "perm_filed":    ["perm", "labor-certification", "dol"],
    "i140_filed":    ["i140", "i-140", "immigrant-petition"],
    "i140_approved": ["i140", "i-140", "priority-date", "visa-bulletin"],
    "i485_filed":    ["i485", "i-485", "adjustment-of-status", "ead", "advance-parole", "ap-ead"],
}

ALERT_THRESHOLD = 7.0


@dataclass
class MatchResult:
    change: RuleChange
    score: float
    reasons: list[str]


def score_change(user: User, change: RuleChange) -> MatchResult:
    score = 0.0
    reasons: list[str] = []
    change_tags = {t.lower() for t in (change.tags or [])}
    change_visas = {v.upper() for v in (change.visa_categories_affected or [])}

    # ---- 1. Direct visa category match (highest weight) ----
    user_visas: set[str] = set()
    if user.primary_visa_type:
        user_visas.add(user.primary_visa_type.upper())
    for v in user.visa_categories or []:
        user_visas.add(v.upper())

    direct_match = user_visas & change_visas
    if direct_match or "ALL" in change_visas:
        score += 10.0
        label = ", ".join(sorted(direct_match or user_visas))
        reasons.append(f"Directly affects your {label} status")
    else:
        # Tag-based secondary match for the primary visa
        for visa in user_visas:
            visa_tags = set(_VISA_TAG_MAP.get(visa, []))
            if visa_tags & change_tags:
                score += 6.0
                reasons.append(f"Relevant to your {visa} via policy tags")
                break

    # ---- 2. Third-party / consulting placement ----
    if user.placement_type == "third_party" and change_tags & {"site-visits", "third-party-placement", "bench", "lca"}:
        score += 5.0
        reasons.append("You work at a third-party client site — site visit rules apply to you")

    # ---- 3. OPT / STEM OPT ----
    if user.on_opt:
        if user.opt_type == "stem" and change_tags & {"stem-opt", "stem", "stem-extension"}:
            score += 6.0
            reasons.append("You're on STEM OPT extension")
        elif change_tags & {"opt", "f1-opt", "optional-practical-training"}:
            score += 5.0
            reasons.append("You're currently on OPT")

    # ---- 4. H-4 EAD dependent ----
    dependents = {d.upper() for d in (user.dependent_visa_types or [])}
    if "H-4 EAD" in dependents and change_tags & {"h4-ead", "h-4-ead", "h4-work-authorization"}:
        score += 4.0
        reasons.append("Your dependent holds H-4 EAD work authorization")
    if "H-4" in dependents and change_tags & {"h4", "h-4"}:
        score += 2.0
        reasons.append("You have an H-4 dependent")

    # ---- 5. Green card stage ----
    if user.gc_stage and user.gc_stage != "none":
        gc_tags = set(_GC_STAGE_TAG_MAP.get(user.gc_stage, []))
        if gc_tags & change_tags:
            score += 5.0
            label = user.gc_stage.replace("_", " ")
            reasons.append(f"Affects your GC stage: {label}")

    # ---- 6. Country of birth (EB backlog) ----
    if user.country_of_birth in ("India", "China") and change_tags & {
        "priority-date", "visa-bulletin", "retrogression", "backlog", "eb-backlog"
    }:
        score += 4.0
        reasons.append(f"Affects priority dates for {user.country_of_birth}-born applicants")

    # ---- 7. Employer type ----
    if user.employer_type in ("consulting", "staffing") and change_tags & {
        "site-visits", "third-party-placement", "lca", "prevailing-wage", "worksite"
    }:
        score += 3.0
        reasons.append("Affects consulting/staffing H-1B arrangements")

    if user.employer_type == "nonprofit" and change_tags & {"cap-exempt", "nonprofit", "university"}:
        score += 3.0
        reasons.append("Affects cap-exempt nonprofit employers")

    # ---- 8. Specialty occupation + degree field ----
    if user.primary_visa_type == "H-1B" and change_tags & {"specialty-occupation", "degree-requirement"}:
        if user.degree_field:
            score += 2.0
            reasons.append(f"May affect the degree requirement for your field ({user.degree_field})")

    # ---- Impact level multiplier ----
    multiplier = {"high": 1.5, "medium": 1.2, "low": 1.0}.get(change.impact_level, 1.0)
    score *= multiplier

    return MatchResult(change=change, score=round(score, 2), reasons=reasons)


def match_changes_for_user(
    user: User,
    changes: list[RuleChange],
    threshold: float = ALERT_THRESHOLD,
) -> list[MatchResult]:
    min_level_order = {"low": 0, "medium": 1, "high": 2}
    user_min = min_level_order.get(user.min_impact_level or "medium", 1)

    results = []
    for change in changes:
        if min_level_order.get(change.impact_level, 0) < user_min:
            continue
        result = score_change(user, change)
        if result.score >= threshold:
            results.append(result)

    results.sort(key=lambda r: r.score, reverse=True)
    return results
