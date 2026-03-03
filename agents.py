import gspread
from google.oauth2.service_account import Credentials
import os
import json
import datetime


def create_and_fill_sheet(data):

    try:
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

        # Unique tab name to avoid duplicate errors
        tab_name = "Course_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        worksheet = sheet.add_worksheet(
            title=tab_name,
            rows="200",
            cols="20"
        )

        worksheet.update("A1", [["Curriculum Test Output"]])
        worksheet.update("A2", [[json.dumps(data, indent=2)]])

        return sheet.url

    except Exception as e:
        print("SHEET ERROR:", str(e))
        raise e
