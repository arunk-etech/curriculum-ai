from fastapi import FastAPI
from agents import run_all_agents
from sheets import create_and_fill_sheet

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Curriculum AI running"}

@app.post("/generate")
def generate_course(data: dict):
    results = run_all_agents(data)
    sheet_url = create_and_fill_sheet(results)
    return {"sheet_url": sheet_url}
