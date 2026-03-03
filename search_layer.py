import os
import requests
from typing import List, Dict


def web_search_serpapi(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Uses SerpAPI (Google) and returns a list of:
    [{title, url, snippet, source}, ...]
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("SERPAPI_KEY is not set in environment variables")

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num_results,
    }

    r = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("organic_results", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "source": item.get("source", ""),
        })

    return results


def build_course_search_context(course_name: str, grade: str, skill_focus_21st: str) -> dict:
    """
    Course-level search context you can attach once for Agent 2–5 (not per activity).
    Keep it small to avoid token bloat.
    """
    grade = grade or ""
    skill_focus_21st = skill_focus_21st or ""

    queries = {
        "research_sources": [
            f"{course_name} grade {grade} pedagogy evidence",
            f"{skill_focus_21st} middle school education evidence",
            "cognitive science retrieval practice spaced practice classroom evidence",
        ],
        "govt_sources": [
            "NEP 2020 competency based education experiential learning official PDF",
            "NCERT learning outcomes middle school computational thinking",
            "SCERT curriculum framework middle school India",
        ],
        "international_sources": [
            "UNICEF life skills framework PDF",
            "Skills Builder Universal Framework PDF",
            "UN SDG 4 quality education targets official",
        ],
        "studies_sources": [
            f"computational thinking grade {grade} study",
            "pair programming middle school study",
            "debugging novice programmers study",
        ],
    }

    ctx = {}
    for key, qlist in queries.items():
        merged = []
        for q in qlist:
            merged.extend(web_search_serpapi(q, num_results=4))
        # keep only top ~10 per section to avoid huge payloads
        ctx[key] = merged[:10]

    return ctx
