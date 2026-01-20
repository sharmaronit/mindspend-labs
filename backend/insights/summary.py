from typing import List, Dict
from models.schema import Transaction, BehaviorPattern, Trigger, Insight


def make_summary(transactions: List[Transaction], patterns: List[BehaviorPattern], triggers: List[Trigger], insights: List[Insight]) -> Dict:
    pattern_counts: Dict[str, int] = {}
    for p in patterns:
        pattern_counts[p.type] = pattern_counts.get(p.type, 0) + 1
    trigger_factors = sorted({t.factor for t in triggers})
    return {
        "transactions": len(transactions),
        "patterns": pattern_counts,
        "triggers": trigger_factors,
        "insights_count": len(insights),
    }
