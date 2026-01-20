from typing import Any, Dict, Optional
from datetime import datetime

class SheetsClient:
    """Google Sheets adapter with graceful fallback to stub.

    If `gspread` is installed and credentials are provided, writes to a real spreadsheet.
    Otherwise, returns a stub URL.
    """

    def __init__(self, credentials_json: Optional[str] = None):
        self.credentials_json = credentials_json
        self._gspread = None
        self._client = None
        try:
            import gspread  # type: ignore
            self._gspread = gspread
            if credentials_json:
                self._client = gspread.service_account(filename=credentials_json)
        except Exception:
            self._gspread = None
            self._client = None

    def export_summary(self, user_id: str, summary: Dict[str, Any]) -> str:
        """Export summary to a sheet and return a URL.

        Real mode: creates/opens a spreadsheet named `PFBA_{user_id}` and appends a row.
        Stub mode: returns a fake URL.
        """
        if self._client is None:
            return f"https://sheets.local/stub/{user_id}/summary"
        title = f"PFBA_{user_id}"
        # Try open; else create
        try:
            sh = self._client.open(title)
        except Exception:
            sh = self._client.create(title)
        try:
            ws = sh.sheet1
        except Exception:
            ws = sh.add_worksheet(title="Summary", rows=100, cols=20)
        # Append timestamped summary key-values
        ts = datetime.utcnow().isoformat()
        row = [ts] + [f"{k}={summary.get(k)}" for k in sorted(summary.keys())]
        ws.append_row(row)
        return sh.url
