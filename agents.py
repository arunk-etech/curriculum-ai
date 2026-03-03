from openai import OpenAI
import os
import json

MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")
    return OpenAI(api_key=api_key)


def _extract_json_object(text: str) -> str:
    """
    Extract the first top-level JSON object from a messy string.
    Handles cases like:
    - ```json ... ```
    - extra commentary before/after
    """
    if not text:
        return ""

    t = text.strip()

    # Strip markdown code fences
    if t.startswith("```"):
        # Remove the first fence line (``` or ```json)
        lines = t.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            t = "\n".join(lines[1:])
        # Remove ending fence if present
        if t.strip().endswith("```"):
            t = t.strip()[:-3].strip()

    # Find first '{' and last '}' to extract a JSON object
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return t

    return t[start:end + 1]


def _try_parse_json(text: str) -> dict:
    cleaned = _extract_json_object(text)
    return json.loads(cleaned)


def _repair_json_once(client: OpenAI, bad_text: str) -> dict:
    repair_prompt = """
Fix the following into VALID JSON ONLY (no markdown, no commentary).

Schema (must match exactly; no extra keys):
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
- Output MUST be a single JSON object.
- Fill missing fields with "N/A".
- Keep english_script concise (5–8 lines).
"""

    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": repair_prompt},
            {"role": "user", "content": bad_text}
        ],
        temperature=0.0,
        max_tokens=1400,
    )

    return _try_parse_json(resp.choices[0].message.content)


def _repair_json(client: OpenAI, bad_text: str) -> dict:
    """
    Try repair twice (sometimes first repair still has minor issues).
    """
    try:
        return _repair_json_once(client, bad_text)
    except Exception:
        # Second repair attempt (even stricter)
        return _repair_json_once(client, bad_text)


def run_all_agents(input_data: dict) -> dict:
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
- "units" MUST be an array.
- Each unit has "unit_title" and "activities" (array).
- Each activity has ALL 9 fields listed above.
- No extra keys.
- Generate EXACTLY input_data["units"] units.
- Generate EXACTLY input_data["activities_per_unit"] activities per unit.
- Keep english_script concise (5–8 lines).
"""

    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_data)}
        ],
        temperature=0.2,
        max_tokens=1600,
    )

    raw = resp.choices[0].message.content

    # Parse first
    try:
        parsed = _try_parse_json(raw)
    except Exception:
        parsed = _repair_json(client, raw)

    # Defensive normalization so sheets.py never crashes
    if not isinstance(parsed, dict):
        parsed = {"units": []}
    if "units" not in parsed or not isinstance(parsed["units"], list):
        parsed["units"] = []

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
