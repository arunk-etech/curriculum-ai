import gspread
from google.oauth2.service_account import Credentials
import os
import json
import re


def _gc():
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found")

    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )
    return gspread.authorize(creds)


def extract_sheet_id(url: str) -> str:
    """
    Extracts spreadsheet ID from Google Sheets URL.
    """
    if not url:
        return ""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return m.group(1) if m else ""


def sheet_to_text(sheet_url: str, tab_name: str) -> str:
    """
    Reads a tab and converts rows into plain text for GPT.
    """
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError(f"Invalid Google Sheet URL: {sheet_url}")

    gc = _gc()
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(tab_name)

    records = ws.get_all_records()

    # Convert rows to compact text
    lines = []
    for r in records:
        parts = [f"{k}: {v}" for k, v in r.items() if str(v).strip()]
        if parts:
            lines.append(" | ".join(parts))

    return "\n".join(lines)
