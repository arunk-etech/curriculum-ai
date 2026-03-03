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

        headers = [
            "Unit No.",
            "Unit Title",
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

        for unit_no, unit in enumerate(data["units"], start=1):
            unit_title = unit.get("unit_title", f"Unit {unit_no}")
            activities = unit.get("activities", [])
            if not isinstance(activities, list):
                continue

            for activity_no, a in enumerate(activities, start=1):
                if not isinstance(a, dict):
                    continue

                rows.append([
                    unit_no,
                    unit_title,
                    activity_no,
                    a.get("activity_name", "N/A"),
                    a.get("description", "N/A"),
                    a.get("objective", "N/A"),
                    a.get("outcomes", "N/A"),
                    a.get("content_knowledge", "N/A"),
                    a.get("skills_21st", "N/A"),
                    a.get("sdg_aligned", "N/A"),
                    a.get("materials_required", "N/A"),
                ])

        # Fast write
        worksheet.update("A1", rows)

        # ---------- Formatting (Freeze + Colors) ----------
        sheet_id = worksheet.id

        # Colors use 0..1 floats
        light_yellow = {"red": 1.0, "green": 1.0, "blue": 0.8}
        light_blue = {"red": 0.80, "green": 0.90, "blue": 1.0}

        sheet.batch_update({
            "requests": [
                # Freeze row 1 and first 3 columns (A-C)
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {
                                "frozenRowCount": 1,
                                "frozenColumnCount": 3
                            }
                        },
                        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"
                    }
                },
                # Header row background = light yellow (row 1)
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": light_yellow,
                                "textFormat": {"bold": True}
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat.bold)"
                    }
                },
                # Columns A-C background = light blue (all rows)
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startColumnIndex": 0,
                            "endColumnIndex": 3
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": light_blue
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                },
            ]
        })

        return sheet.url

    except Exception as e:
        print("SHEET ERROR:", str(e))
        raise e
