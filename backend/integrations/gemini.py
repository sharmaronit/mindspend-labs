from typing import Any, Dict, List, Optional
from models.schema import Insight

class GeminiClient:
    """Stubbed Gemini adapter.

    Replace with actual Gemini API calls to generate insight phrasing/coaching.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def generate_insight_text(self, context: Dict[str, Any]) -> str:
        # TODO: call Gemini; for now, return a templated message
        return "Based on your recent patterns, consider simple caps and cooldowns to reduce impulse purchases."

    def enhance_insights(self, insights: List[Insight]) -> List[Insight]:
        # Stub: augment detail field with a generic line
        updated: List[Insight] = []
        for i in insights:
            if not i.detail:
                i.detail = self.generate_insight_text({"summary": i.summary})
            updated.append(i)
        return updated
