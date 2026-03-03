from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from agents import run_all_agents
from sheets import create_and_fill_sheet
from config_reader import sheet_to_text  # <- you must add config_reader.py

app = FastAPI()


class CourseInput(BaseModel):
    course_name: str
    grade: str
    units: int
    activities_per_unit: int

    activity_types: Optional[List[str]] = None
    skill_focus_21st: Optional[str] = None

    # Old optional fields (keep if you want)
    frameworks: Optional[List[str]] = None
    rubric_description: Optional[str] = None

    # ✅ New: Google Sheet links
    framework_sheet_url: Optional[str] = None
    rubric_sheet_url: Optional[str] = None

    # Extra constraints like “3-4 min video”
    special_instructions: Optional[str] = None


@app.get("/")
def home():
    return {"status": "Curriculum AI running"}


@app.post("/generate")
def generate_course(data: CourseInput):
    payload = data.model_dump()

    # If a framework sheet link is given, read it and pass it to GPT
    if payload.get("framework_sheet_url"):
        payload["framework_text"] = sheet_to_text(payload["framework_sheet_url"], "Framework")

    # If a rubric sheet link is given, read it and pass it to GPT
    if payload.get("rubric_sheet_url"):
        payload["rubric_text"] = sheet_to_text(payload["rubric_sheet_url"], "Rubric")

    results = run_all_agents(payload)
    sheet_url = create_and_fill_sheet(results)
    return {"sheet_url": sheet_url}
