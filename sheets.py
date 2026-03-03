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

        # 🔥 REPLACE THIS
        spreadsheet_id = "1Ndd3mFpraoFgMZv72l8gNIo6O5BZtj5pZtE8VodtR9w"

        sheet = gc.open_by_key(spreadsheet_id)

        # Create unique tab
        tab_name = "Course_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        worksheet = sheet.add_worksheet(
            title=tab_name,
            rows="1000",
            cols="20"
        )

        # Validate structure
        if "units" not in data:
            raise ValueError("No 'units' key found in curriculum")

        # Write headers
        headers = [
            "Unit Title",
            "Activity Title",
            "Objective",
            "21st Century Skill",
            "Assessment"
        ]

        worksheet.append_row(headers)

        # Write curriculum rows
        for unit in data["units"]:

            unit_title = unit.get("unit_title", "N/A")
            activities = unit.get("activities", [])

            for activity in activities:

                row = [
                    unit_title,
                    activity.get("activity_title", "N/A"),
                    activity.get("objective", "N/A"),
                    activity.get("21st_century_skill", "N/A"),
                    activity.get("assessment", "N/A")
                ]

                worksheet.append_row(row)

        return sheet.url

    except Exception as e:
        print("SHEET ERROR:", str(e))
        raise e
