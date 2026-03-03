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

    # Use spreadsheet ID instead of name
    sheet = gc.open_by_key("PASTE_YOUR_SPREADSHEET_ID_HERE")

    # Create new worksheet tab per generation
    worksheet = sheet.add_worksheet(
        title="Course_Output",
        rows="200",
        cols="20"
    )

    worksheet.update("A1", [["Curriculum Data"]])
    worksheet.update("A2", [[str(data)]])

    return sheet.url
