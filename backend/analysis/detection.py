from typing import List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from models.schema import Transaction, BehaviorPattern, Trigger, AnalysisResult

DISCRETIONARY_CATEGORIES = {"shopping", "entertainment", "dining", "food", "travel"}


def _is_weekend(dt: datetime) -> bool:
    return dt.weekday() >= 5  # 5=Sat, 6=Sun


def _time_bucket(dt: datetime) -> str:
    h = dt.hour
    if 0 <= h < 5:
        return "late-night"
    if 5 <= h < 12:
        return "morning"
    if 12 <= h < 17:
        return "afternoon"
    return "evening"


def analyze_transactions(transactions: List[Transaction]) -> AnalysisResult:
    # Derive simple tags
    for t in transactions:
        tags = set(t.derived_tags or [])
        bucket = _time_bucket(t.date)
        tags.add(bucket)
        if _is_weekend(t.date):
            tags.add("weekend")
        if t.base_category in DISCRETIONARY_CATEGORIES:
            tags.add("discretionary")
        t.derived_tags = list(tags)

    patterns: List[BehaviorPattern] = []
    triggers: List[Trigger] = []

    # Binge cycles: ≥3 discretionary in ≤6 hours
    discretionary = [t for t in transactions if "discretionary" in t.derived_tags]
    discretionary.sort(key=lambda x: x.date)
    n = len(discretionary)
    i = 0
    while i < n:
        j = i
        while j < n and (discretionary[j].date - discretionary[i].date) <= timedelta(hours=6):
            j += 1
        window = discretionary[i:j]
        if len(window) >= 3:
            confidence = min(1.0, 0.3 + 0.1 * len(window))
            patterns.append(
                BehaviorPattern(
                    id=None,
                    user_id=None,
                    type="binge",
                    confidence=confidence,
                    period=(window[0].date, window[-1].date),
                    supporting_evidence=[k for k in range(len(window))],
                )
            )
        i += 1

    # Weekend trigger: elevated discretionary on weekends
    weekend_spend = sum(t.amount for t in transactions if "weekend" in t.derived_tags and "discretionary" in t.derived_tags)
    weekday_spend = sum(t.amount for t in transactions if "weekend" not in t.derived_tags and "discretionary" in t.derived_tags)
    weekend_ratio = (weekend_spend + 1) / (weekday_spend + 1)
    if weekend_ratio > 1.3 and weekend_spend > 0:
        triggers.append(
            Trigger(
                id=None,
                user_id=None,
                factor="weekend",
                signal_strength=min(1.0, weekend_ratio / 2.0),
                correlations={"weekend_spend": weekend_spend, "weekday_spend": weekday_spend},
            )
        )

    # Payday trigger (heuristic): if high discretionary spend near the 1st or 15th
    def _is_payday(dt: datetime) -> bool:
        return dt.day in (1, 15)

    near_payday_spend = sum(
        t.amount for t in discretionary if abs(t.date.day - (1 if t.date.day <= 8 else 15)) <= 2
    )
    if near_payday_spend > 0 and near_payday_spend > (weekday_spend + weekend_spend) * 0.2:
        triggers.append(
            Trigger(
                id=None,
                user_id=None,
                factor="payday",
                signal_strength=min(1.0, near_payday_spend / (weekday_spend + weekend_spend + 1)),
                correlations={"near_payday_spend": near_payday_spend},
            )
        )

    # Aggregate result
    return AnalysisResult(patterns=patterns, triggers=triggers)
