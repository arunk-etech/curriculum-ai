from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from agents import run_all_agents
from sheets import create_and_fill_sheet

app = FastAPI()


class CourseInput(BaseModel):
    course_name: str
    grade: str
    units: int
    activities_per_unit: int

    activity_types: Optional[List[str]] = None
    skill_focus_21st: Optional[str] = None
    frameworks: Optional[List[str]] = None
    rubric_description: Optional[str] = None
    special_instructions: Optional[str] = None


@app.get("/")
def home():
    return {"status": "Curriculum AI running"}


@app.post("/generate")
def generate_course(data: CourseInput):
    results = run_all_agents(data.model_dump())
    sheet_url = create_and_fill_sheet(results)
    return {"sheet_url": sheet_url}
