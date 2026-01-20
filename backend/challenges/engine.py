from typing import List
from models.schema import Insight, Challenge


def propose_challenges(insights: List[Insight]) -> List[Challenge]:
    challenges: List[Challenge] = []
    for ins in insights:
        if "binge" in (ins.linked_patterns or []):
            challenges.append(
                Challenge(
                    id=None,
                    user_id=None,
                    goal="Reduce binge cycles",
                    rules={"cooldown_hours": 48, "max_discretionary_in_window": 2},
                    duration="2 weeks",
                    status="proposed",
                )
            )
        if "weekend" in (ins.linked_patterns or []):
            challenges.append(
                Challenge(
                    id=None,
                    user_id=None,
                    goal="Cap weekend discretionary spend",
                    rules={"weekend_cap": 50},
                    duration="1 week",
                    status="proposed",
                )
            )
        if "payday" in (ins.linked_patterns or []):
            challenges.append(
                Challenge(
                    id=None,
                    user_id=None,
                    goal="Post-payday delay",
                    rules={"purchase_delay_hours": 48},
                    duration="1 week",
                    status="proposed",
                )
            )
    return challenges
