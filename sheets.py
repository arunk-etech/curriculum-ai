import gspread
from google.oauth2.service_account import Credentials
import os
import json
import datetime


def _apply_wrap_only(sheet, worksheet):
    """
    Apply WRAP text to the entire worksheet (all cells).
    """
    sheet_id = worksheet.id
    sheet.batch_update({
        "requests": [
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id},
                    "cell": {
                        "userEnteredFormat": {
                            "wrapStrategy": "WRAP"
                        }
                    },
                    "fields": "userEnteredFormat.wrapStrategy"
                }
            }
        ]
    })


def _apply_curriculum_format(sheet, worksheet):
    """
    Curriculum-only formatting:
    - Freeze row 1
    - Freeze columns A–C
    - Header row background light yellow + bold
    - Columns A–C background light blue
    """
    sheet_id = worksheet.id
    light_yellow = {"red": 1.0, "green": 1.0, "blue": 0.8}
    light_blue = {"red": 0.80, "green": 0.90, "blue": 1.0}

    sheet.batch_update({
        "requests": [
            # Freeze header row and first 3 columns
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
            # Header row background (row 1) + bold
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
                            "textFormat": {"bold": True},
                            "wrapStrategy": "WRAP"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat.bold,wrapStrategy)"
                }
            },
            # Columns A-C background (all rows)
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startColumnIndex": 0,
                        "endColumnIndex": 3
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": light_blue,
                            "wrapStrategy": "WRAP"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,wrapStrategy)"
                }
            },
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

    # Wrap everywhere on Curriculum + apply special formatting ONLY here
    _apply_wrap_only(sheet, cur_ws)
    _apply_curriculum_format(sheet, cur_ws)

    # ---------------- Research tab (Agent 2) ----------------
    res_ws = sheet.add_worksheet(title=f"{stamp}_Research", rows="2500", cols="25")
    research = data.get("research", {})

    res_rows = [
        ["Course Research Summary", research.get("summary", "")],
        ["", ""],
        ["Unit No.", "Unit Title", "Why this sequence", "Pedagogy", "Cognitive principle"],
    ]

    for r in research.get("unit_rationales", []):
        res_rows.append([
            r.get("unit_no", ""),
            r.get("unit_title", ""),
            r.get("why_this_sequence", ""),
            r.get("pedagogy", ""),
            r.get("cognitive_principle", ""),
        ])

    # Course-level citations (not per activity)
    res_rows.append(["", ""])
    res_rows.append(["Citations (course-level)", ""])
    for c in research.get("citations", []):
        res_rows.append([c.get("title", ""), c.get("url", "")])

    res_ws.update("A1", res_rows)
    _apply_wrap_only(sheet, res_ws)

    # ---------------- Govt Alignment tab (Agent 3) ----------------
    gov_ws = sheet.add_worksheet(title=f"{stamp}_Govt_Alignment", rows="3000", cols="25")
    govt = data.get("govt_alignment", {})

    gov_rows = [
        ["Govt Alignment Notes (course-level)", ""],
        ["", ""],
        ["Unit No.", "Activity No.", "Alignment", "Standard Reference"],
    ]

    for row in govt.get("rows", []):
        gov_rows.append([
            row.get("unit_no", ""),
            row.get("activity_no", ""),
            row.get("alignment", ""),
            row.get("standard_reference", ""),
        ])

    gov_rows.append(["", ""])
    gov_rows.append(["Citations (course-level)", ""])
    for c in govt.get("citations", []):
        gov_rows.append([c.get("title", ""), c.get("url", "")])

    gov_ws.update("A1", gov_rows)
    _apply_wrap_only(sheet, gov_ws)

    # ---------------- International Alignment tab (Agent 4) ----------------
    intl_ws = sheet.add_worksheet(title=f"{stamp}_International_Alignment", rows="3000", cols="30")
    intl = data.get("international_alignment", {})

    intl_rows = [
        ["International Alignment Notes (course-level)", ""],
        ["", ""],
        ["Unit No.", "Activity No.", "UNICEF Life Skill", "Skills Builder Skill", "SDG"],
    ]

    for row in intl.get("rows", []):
        intl_rows.append([
            row.get("unit_no", ""),
            row.get("activity_no", ""),
            row.get("unicef_life_skill", ""),
            row.get("skills_builder_skill", ""),
            row.get("sdg", ""),
        ])

    intl_rows.append(["", ""])
    intl_rows.append(["Citations (course-level)", ""])
    for c in intl.get("citations", []):
        intl_rows.append([c.get("title", ""), c.get("url", "")])

    intl_ws.update("A1", intl_rows)
    _apply_wrap_only(sheet, intl_ws)

    # ---------------- Studies tab (Agent 5) ----------------
    stu_ws = sheet.add_worksheet(title=f"{stamp}_Studies", rows="3000", cols="30")
    studies = data.get("studies", {})

    stu_rows = [
        ["Studies Summary (course-level)", ""],
        ["", ""],
        ["Topic", "What it says", "Age/Grade", "How to use in class", "URL"],
    ]

    for s in studies.get("studies", []):
        stu_rows.append([
            s.get("topic", ""),
            s.get("what_it_says", ""),
            s.get("age_grade", ""),
            s.get("how_to_use_in_class", ""),
            s.get("url", ""),
        ])

    stu_rows.append(["", ""])
    stu_rows.append(["Citations (course-level)", ""])
    for c in studies.get("citations", []):
        stu_rows.append([c.get("title", ""), c.get("url", "")])

    stu_ws.update("A1", stu_rows)
    _apply_wrap_only(sheet, stu_ws)

    return sheet.url
