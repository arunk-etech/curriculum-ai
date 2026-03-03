import gspread
from google.oauth2.service_account import Credentials
import os
import json
import datetime


def create_and_fill_sheet(data):

    try:
        # Load Google credentials
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

        # ✅ Your master spreadsheet ID (already shared with service account)
        spreadsheet_id = "1Ndd3mFpraoFgMZv72l8gNIo6O5BZtj5pZtE8VodtR9w"
        sheet = gc.open_by_key(spreadsheet_id)

        # Create unique tab
        tab_name = "Course_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        worksheet = sheet.add_worksheet(title=tab_name, rows="2000", cols="20")

        # Validate structure
        if not isinstance(data, dict) or "units" not in data or not isinstance(data["units"], list):
            raise ValueError("Invalid curriculum format: expected {'units': [...]}")

        # Headers exactly as requested
        headers = [
            "Activity Name",
            "Description",
            "Objective",
            "Outcomes",
            "Content Knowledge",
            "21st Century Skills",
            "SDG Aligned",
            "Material Required",
            "English Script",
        ]
        worksheet.append_row(headers)

        # Write rows (one per activity)
        for unit in data["units"]:
            activities = unit.get("activities", [])
            if not isinstance(activities, list):
                continue

            for activity in activities:
                if not isinstance(activity, dict):
                    continue

                row = [
                    activity.get("activity_name", "N/A"),
                    activity.get("description", "N/A"),
                    activity.get("objective", "N/A"),
                    activity.get("outcomes", "N/A"),
                    activity.get("content_knowledge", "N/A"),
                    activity.get("skills_21st", "N/A"),
                    activity.get("sdg_aligned", "N/A"),
                    activity.get("materials_required", "N/A"),
                    activity.get("english_script", "N/A"),
                ]
                worksheet.append_row(row)

        return sheet.url

    except Exception as e:
        print("SHEET ERROR:", str(e))
        raise e
