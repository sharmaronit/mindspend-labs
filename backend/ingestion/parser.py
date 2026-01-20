from typing import List
from models.schema import Transaction
import csv
import io
from datetime import datetime

SCHEMA = ["date", "merchant", "amount", "base_category", "notes"]


def parse_csv_bytes(content: bytes) -> List[Transaction]:
    text = content.decode("utf-8", errors="ignore")
    return parse_csv_text(text)


def parse_csv_text(text: str) -> List[Transaction]:
    reader = csv.DictReader(io.StringIO(text))
    # Try to standardize headers by lowercasing
    field_map = {f.lower(): f for f in reader.fieldnames or []}

    def get(row, key):
        # Support common variants like Date, Amount, Merchant
        for k in [key, key.title(), key.upper()]:
            if k in row:
                return row[k]
        # Fallback to lowercased matching
        lk = key.lower()
        for k in row.keys():
            if k.lower() == lk:
                return row[k]
        return None

    transactions: List[Transaction] = []
    for row in reader:
        date_str = get(row, "date") or get(row, "transaction_date")
        if not date_str:
            # Skip rows without a date
            continue
        merchant = (get(row, "merchant") or get(row, "description") or "").strip()
        amount_str = get(row, "amount") or get(row, "debit") or get(row, "credit")
        base_category = (get(row, "base_category") or get(row, "category") or "uncategorized").strip().lower()
        notes = (get(row, "notes") or "").strip()

        # Parse date and amount safely
        try:
            dt = datetime.fromisoformat(date_str)
        except Exception:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                try:
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                except Exception:
                    try:
                        dt = datetime.strptime(date_str, "%m/%d/%Y")
                    except Exception:
                        # Skip unparseable dates
                        continue

        amt = 0.0
        if amount_str is not None:
            s = amount_str.replace(",", "").strip()
            try:
                amt = float(s)
            except Exception:
                amt = 0.0

        transactions.append(
            Transaction(
                id=None,
                user_id=None,
                date=dt,
                amount=amt,
                merchant=merchant,
                base_category=base_category,
                source="csv",
                notes=notes,
                derived_tags=[],
            )
        )

    return transactions
