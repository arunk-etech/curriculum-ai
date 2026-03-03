from openai import OpenAI
import os
import json


MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")
    return OpenAI(api_key=api_key)


def _try_parse_json(text: str):
    text = text.strip()

    # Remove common wrappers if model adds them
    if text.startswith("```"):
        text = text.strip("`")
        # Sometimes it starts with ```json
        text = text.replace("json", "", 1).strip()

    return json.loads(text)


def _repair_json(client: OpenAI, bad_text: str) -> dict:
    """
    Second call: ask model to repair into valid JSON only.
    Keep this short and deterministic.
    """
    repair_prompt = """
You will be given text that is intended to be JSON but is invalid.
Convert it into VALID JSON that matches this schema exactly:

{
  "units": [
    {
      "unit_title": "string",
      "activities": [
        {
          "activity_title": "string",
          "objective": "string",
          "21st_century_skill": "string",
          "assessment": "string"
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
        max_tokens=1200,
        response_format={"type": "json_object"},
    )

    repaired = resp.choices[0].message.content
    return _try_parse_json(repaired)


def run_all_agents(input_data: dict) -> dict:
    """
    Single-agent MVP:
    Creates a structured curriculum JSON that sheets.py can write.
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
          "activity_title": "string",
          "objective": "string",
          "21st_century_skill": "string",
          "assessment": "string"
        }
      ]
    }
  ]
}

Hard constraints:
- units must be an ARRAY (list) of unit objects.
- Each unit must have "unit_title" and "activities" (array).
- Each activity must have all four fields.
- No extra keys.
- Keep it concise: for each unit generate EXACTLY input_data["activities_per_unit"] activities.
- Generate EXACTLY input_data["units"] units.
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_data)}
        ],
        temperature=0.2,
        max_tokens=1400,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content

    # 1st parse attempt
    try:
        parsed = _try_parse_json(raw)
    except Exception:
        # Repair if invalid
        parsed = _repair_json(client, raw)

    # Final validation guard (prevents the exact error you saw)
    if not isinstance(parsed, dict) or "units" not in parsed or not isinstance(parsed["units"], list):
        # last resort: wrap into minimal valid structure
        parsed = {"units": []}

    # Enforce unit/activity counts defensively
    units_target = int(input_data.get("units", 1))
    acts_target = int(input_data.get("activities_per_unit", 1))

    parsed["units"] = parsed["units"][:units_target]
    for u in parsed["units"]:
        if "unit_title" not in u:
            u["unit_title"] = "N/A"
        if "activities" not in u or not isinstance(u["activities"], list):
            u["activities"] = []
        u["activities"] = u["activities"][:acts_target]
        for a in u["activities"]:
            a.setdefault("activity_title", "N/A")
            a.setdefault("objective", "N/A")
            a.setdefault("21st_century_skill", "N/A")
            a.setdefault("assessment", "N/A")

    return parsed
