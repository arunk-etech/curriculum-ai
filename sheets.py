import gspread
from google.oauth2.service_account import Credentials
import os
import json
import datetime


def create_and_fill_sheet(data):

    try:
        # Load service account credentials
        creds_dict = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))

        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )

        gc = gspread.authorize(creds)

        # 🔥 REPLACE THIS WITH YOUR REAL SPREADSHEET ID
        spreadsheet_id = "1Ndd3mFpraoFgMZv72l8gNIo6O5BZtj5pZtE8VodtR9w"

        sheet = gc.open_by_key(spreadsheet_id)

        # Unique worksheet name
        tab_name = "Course_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        worksheet = sheet.add_worksheet(
            title=tab_name,
            rows="500",
            cols="30"
        )

        # ---- Write structured data ---- #

        # If GPT returned proper JSON
        if isinstance(data, dict):

            # Write headers
            worksheet.update("A1", [["Key", "Value"]])

            row = 2
            for key, value in data.items():
                worksheet.update(f"A{row}", [[key, str(value)]])
                row += 1

        else:
            # Fallback if unexpected format
            worksheet.update("A1", [["Raw Output"]])
            worksheet.update("A2", [[str(data)]])

        return sheet.url

    except Exception as e:
        print("SHEET ERROR:", str(e))
        raise e
