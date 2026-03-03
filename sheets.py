import gspread
from google.oauth2.service_account import Credentials
import os
import json
import datetime


def _format_tab(sheet, worksheet):
    sheet_id = worksheet.id
    light_yellow = {"red": 1.0, "green": 1.0, "blue": 0.8}
    light_blue = {"red": 0.80, "green": 0.90, "blue": 1.0}

    sheet.batch_update({
        "requests": [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 3}
                    },
                    "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"backgroundColor": light_yellow, "textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat.bold)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startColumnIndex": 0, "endColumnIndex": 3},
                    "cell": {"userEnteredFormat": {"backgroundColor": light_blue}},
                    "fields": "userEnteredFormat.backgroundColor"
                }
            }
        ]
    })


def create_and_fill_sheet(data):
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

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # ---------------- Curriculum tab ----------------
    cur_ws = sheet.add_worksheet(title=f"{stamp}_Curriculum", rows="4000", cols="25")
    cur_headers = [
        "Unit No.", "Unit Title", "Activity No.",
        "Activity Name", "Description", "Objective", "Outcomes",
        "Content Knowledge", "21st Century Skills", "SDG Aligned", "Material Required"
    ]
    cur_rows = [cur_headers]

    curriculum = data.get("curriculum", {})
    for unit_no, unit in enumerate(curriculum.get("units", []), start=1):
        unit_title = unit.get("unit_title", f"Unit {unit_no}")
        for activity_no, a in enumerate(unit.get("activities", []), start=1):
            cur_rows.append([
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

    cur_ws.update("A1", cur_rows)
    _format_tab(sheet, cur_ws)

    # ---------------- Research tab (Agent 2) ----------------
    res_ws = sheet.add_worksheet(title=f"{stamp}_Research", rows="2000", cols="20")
    res_headers = ["Unit No.", "Unit Title", "Why this sequence", "Pedagogy", "Cognitive principle"]
    res_rows = [res_headers]

    research = data.get("research", {})
    for r in research.get("unit_rationales", []):
        res_rows.append([
            r.get("unit_no", ""),
            r.get("unit_title", ""),
            r.get("why_this_sequence", ""),
            r.get("pedagogy", ""),
            r.get("cognitive_principle", ""),
        ])

    res_rows.append(["", "", "Overall Summary", research.get("summary", ""), ""])
    res_rows.append(["", "", "Citations", "", ""])
    for c in research.get("citations", []):
        res_rows.append(["", "", c.get("title", ""), c.get("url", ""), c.get("note", "")])

    res_ws.update("A1", res_rows)
    _format_tab(sheet, res_ws)

    # ---------------- Govt Alignment tab (Agent 3) ----------------
    gov_ws = sheet.add_worksheet(title=f"{stamp}_Govt_Alignment", rows="2500", cols="20")
    gov_headers = ["Unit No.", "Activity No.", "Alignment", "Standard Reference"]
    gov_rows = [gov_headers]

    govt = data.get("govt_alignment", {})
    for row in govt.get("rows", []):
        gov_rows.append([
            row.get("unit_no", ""),
            row.get("activity_no", ""),
            row.get("alignment", ""),
            row.get("standard_reference", ""),
        ])

    gov_rows.append(["", "", "Citations", ""])
    for c in govt.get("citations", []):
        gov_rows.append(["", "", c.get("title", ""), c.get("url", "")])

    gov_ws.update("A1", gov_rows)
    _format_tab(sheet, gov_ws)

    # ---------------- International Alignment tab (Agent 4) ----------------
    intl_ws = sheet.add_worksheet(title=f"{stamp}_International_Alignment", rows="2500", cols="25")
    intl_headers = ["Unit No.", "Activity No.", "UNICEF Life Skill", "Skills Builder Skill", "SDG"]
    intl_rows = [intl_headers]

    intl = data.get("international_alignment", {})
    for row in intl.get("rows", []):
        intl_rows.append([
            row.get("unit_no", ""),
            row.get("activity_no", ""),
            row.get("unicef_life_skill", ""),
            row.get("skills_builder_skill", ""),
            row.get("sdg", ""),
        ])

    intl_rows.append(["", "", "Citations", "", ""])
    for c in intl.get("citations", []):
        intl_rows.append(["", "", c.get("title", ""), c.get("url", ""), c.get("note", "")])

    intl_ws.update("A1", intl_rows)
    _format_tab(sheet, intl_ws)

    # ---------------- Studies tab (Agent 5) ----------------
    stu_ws = sheet.add_worksheet(title=f"{stamp}_Studies", rows="2500", cols="25")
    stu_headers = ["Topic", "What it says", "Age/Grade", "How to use in class", "URL"]
    stu_rows = [stu_headers]

    studies = data.get("studies", {})
    for s in studies.get("studies", []):
        stu_rows.append([
            s.get("topic", ""),
            s.get("what_it_says", ""),
            s.get("age_grade", ""),
            s.get("how_to_use_in_class", ""),
            s.get("url", ""),
        ])

    stu_rows.append(["Citations", "", "", "", ""])
    for c in studies.get("citations", []):
        stu_rows.append([c.get("title", ""), c.get("url", ""), c.get("note", ""), "", ""])

    stu_ws.update("A1", stu_rows)
    _format_tab(sheet, stu_ws)

    return sheet.url
