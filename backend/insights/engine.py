from typing import List
from models.schema import BehaviorPattern, Trigger, Insight


def synthesize_insights(patterns: List[BehaviorPattern], triggers: List[Trigger]) -> List[Insight]:
    insights: List[Insight] = []
    if any(p.type == "binge" for p in patterns):
        insights.append(
            Insight(
                id=None,
                user_id=None,
                summary="Detected binge spending cycles",
                detail="Multiple discretionary purchases clustered in short windows. Consider cooldown rules and pre-commit budgets.",
                priority=1,
                linked_patterns=["binge"],
            )
        )
    if any(t.factor == "weekend" for t in triggers):
        insights.append(
            Insight(
                id=None,
                user_id=None,
                summary="Weekend trigger detected",
                detail="Discretionary spend is higher on weekends. Try weekend budget caps and planned activities.",
                priority=2,
                linked_patterns=["weekend"],
            )
        )
    if any(t.factor == "payday" for t in triggers):
        insights.append(
            Insight(
                id=None,
                user_id=None,
                summary="Post-payday spike",
                detail="Spend increases near payday. Consider automatic transfers and 48-hour purchase delays.",
                priority=3,
                linked_patterns=["payday"],
            )
        )
    return insights
