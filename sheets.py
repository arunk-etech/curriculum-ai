import gspread
from google.oauth2.service_account import Credentials
import os
import json
import datetime


def create_and_fill_sheet(data):
    try:
        creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not creds_json:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found")

        creds_dict = json.loads(creds_json)

        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )

        gc = gspread.authorize(creds)

        spreadsheet_id = "1Ndd3mFpraoFgMZv72l8gNIo6O5BZtj5pZtE8VodtR9w"
        sheet = gc.open_by_key(spreadsheet_id)

        tab_name = "Course_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        worksheet = sheet.add_worksheet(title=tab_name, rows="3000", cols="25")

        if not isinstance(data, dict) or "units" not in data or not isinstance(data["units"], list):
            raise ValueError("Invalid curriculum format: expected {'units': [...]}")

        # ✅ Headers (Unit + Activity No added before Activity Name)
        headers = [
            "Unit",
            "Activity No.",
            "Activity Name",
            "Description",
            "Objective",
            "Outcomes",
            "Content Knowledge",
            "21st Century Skills",
            "SDG Aligned",
            "Material Required",
        ]

        rows = [headers]

        # Write rows (one per activity)
        for unit_index, unit in enumerate(data["units"], start=1):
            unit_title = unit.get("unit_title", f"Unit {unit_index}")
            activities = unit.get("activities", [])

            if not isinstance(activities, list):
                continue

            for activity_index, a in enumerate(activities, start=1):
                if not isinstance(a, dict):
                    continue

                rows.append([
                    unit_title,                         # Unit
                    activity_index,                     # Activity No.
                    a.get("activity_name", "N/A"),      # Activity Name
                    a.get("description", "N/A"),
                    a.get("objective", "N/A"),
                    a.get("outcomes", "N/A"),
                    a.get("content_knowledge", "N/A"),
                    a.get("skills_21st", "N/A"),
                    a.get("sdg_aligned", "N/A"),
                    a.get("materials_required", "N/A"),
                ])

        # ✅ Fast single call
        worksheet.update("A1", rows)

        return sheet.url

    except Exception as e:
        print("SHEET ERROR:", str(e))
        raise e
