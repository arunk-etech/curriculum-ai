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

    sheet = gc.open_by_key("1fnYVY4gWpx3XE3hthcbXTDi-lByfYa3WX94Lbgr3ezA")

    import datetime
    tab_name = "Course_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    worksheet = sheet.add_worksheet(
        title=tab_name,
        rows="200",
        cols="20"
    )

    worksheet.update("A1", [["Curriculum Data"]])
    worksheet.update("A2", [[str(data)]])

    return sheet.url
