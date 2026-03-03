from openai import OpenAI
import os
import json

MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")
    return OpenAI(api_key=api_key)


def _try_parse_json(text: str) -> dict:
    text = (text or "").strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    return json.loads(text)


def _repair_json(client: OpenAI, bad_text: str) -> dict:
    """
    Second call: repair invalid JSON into valid JSON matching schema exactly.
    """
    repair_prompt = """
You will be given text intended to be JSON but it is invalid.
Convert it into VALID JSON that matches this schema exactly:

{
  "units": [
    {
      "unit_title": "string",
      "activities": [
        {
          "activity_name": "string",
          "description": "string",
          "objective": "string",
          "outcomes": "string",
          "content_knowledge": "string",
          "skills_21st": "string",
          "sdg_aligned": "string",
          "materials_required": "string",
          "english_script": "string"
        }
      ]
    }
  ]
}

Rules:
- Output JSON only (no markdown, no commentary).
- Do not add extra keys.
- If something is missing, fill with "N/A".
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": repair_prompt},
            {"role": "user", "content": bad_text}
        ],
        temperature=0.0,
        max_tokens=1600,
        response_format={"type": "json_object"},
    )

    repaired = resp.choices[0].message.content
    return _try_parse_json(repaired)


def run_all_agents(input_data: dict) -> dict:
    """
    Single-agent MVP:
    Generates curriculum JSON with the activity fields needed for the sheet columns.
    """
    client = _get_client()

    system_prompt = """
You are a curriculum architect.

Return STRICT JSON only matching this schema:

{
  "units": [
    {
      "unit_title": "string",
      "activities": [
        {
          "activity_name": "string",
          "description": "string",
          "objective": "string",
          "outcomes": "string",
          "content_knowledge": "string",
          "skills_21st": "string",
          "sdg_aligned": "string",
          "materials_required": "string",
          "english_script": "string"
        }
      ]
    }
  ]
}

Hard constraints:
- "units" MUST be an array of unit objects.
- Each unit must have "unit_title" and "activities" (array).
- Each activity must have ALL 9 fields listed above.
- No extra keys.
- Generate EXACTLY input_data["units"] units.
- Generate EXACTLY input_data["activities_per_unit"] activities per unit.
- Keep scripts concise (5–10 lines).
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_data)}
        ],
        temperature=0.2,
        max_tokens=1600,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content

    # 1st parse attempt
    try:
        parsed = _try_parse_json(raw)
    except Exception:
        parsed = _repair_json(client, raw)

    # Final validation + defensive normalization
    if not isinstance(parsed, dict) or "units" not in parsed or not isinstance(parsed["units"], list):
        parsed = {"units": []}

    units_target = int(input_data.get("units", 1))
    acts_target = int(input_data.get("activities_per_unit", 1))

    parsed["units"] = parsed["units"][:units_target]
    for u in parsed["units"]:
        if not isinstance(u, dict):
            continue
        u.setdefault("unit_title", "N/A")
        if "activities" not in u or not isinstance(u["activities"], list):
            u["activities"] = []

        u["activities"] = u["activities"][:acts_target]
        for a in u["activities"]:
            if not isinstance(a, dict):
                continue
            a.setdefault("activity_name", "N/A")
            a.setdefault("description", "N/A")
            a.setdefault("objective", "N/A")
            a.setdefault("outcomes", "N/A")
            a.setdefault("content_knowledge", "N/A")
            a.setdefault("skills_21st", "N/A")
            a.setdefault("sdg_aligned", "N/A")
            a.setdefault("materials_required", "N/A")
            a.setdefault("english_script", "N/A")

    return parsed
