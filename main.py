from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
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

    dummy_data = {
        "course_name": data.course_name,
        "grade": data.grade,
        "units": data.units,
        "activities_per_unit": data.activities_per_unit,
        "note": "GPT temporarily disabled for sheet testing"
    }

    sheet_url = create_and_fill_sheet(dummy_data)

    return {"sheet_url": sheet_url}
