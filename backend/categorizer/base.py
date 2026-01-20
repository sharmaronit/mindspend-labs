from typing import Optional

MERCHANT_CATEGORY_HINTS = {
    "uber": "travel",
    "lyft": "travel",
    "mcdonald": "food",
    "starbucks": "food",
    "amazon": "shopping",
    "netflix": "entertainment",
    "cinema": "entertainment",
}


def guess_category(merchant: str, fallback: Optional[str] = "uncategorized") -> str:
    m = merchant.lower()
    for k, v in MERCHANT_CATEGORY_HINTS.items():
        if k in m:
            return v
    return fallback or "uncategorized"
