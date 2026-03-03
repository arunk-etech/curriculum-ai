import gspread
from google.oauth2.service_account import Credentials
import os
import json
import datetime


def create_and_fill_sheet(data):

    creds_dict = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    gc = gspread.authorize(creds)

    spreadsheet_id = "PASTE_YOUR_SPREADSHEET_ID_HERE"
    sheet = gc.open_by_key(spreadsheet_id)

    tab_name = "Course_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    worksheet = sheet.add_worksheet(
        title=tab_name,
        rows="1000",
        cols="20"
    )

    # Header row
    headers = [
        "Unit",
        "Activity",
        "Objective",
        "21st Century Skill",
        "Assessment"
    ]

    worksheet.append_row(headers)

    # Fill curriculum
    for unit in data["units"]:
        unit_title = unit["unit_title"]

        for activity in unit["activities"]:
            row = [
                unit_title,
                activity["activity_title"],
                activity["objective"],
                activity["21st_century_skill"],
                activity["assessment"]
            ]

            worksheet.append_row(row)

    return sheet.url
