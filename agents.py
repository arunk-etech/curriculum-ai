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
    if not text:
        return ""
    t = text.strip()

    # Remove markdown fences if any
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            t = "\n".join(lines[1:])
        if t.strip().endswith("```"):
            t = t.strip()[:-3].strip()

    # Extract first JSON object block
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return t
    return t[start:end + 1]


def _try_parse_json(text: str) -> dict:
    cleaned = _extract_json_object(text)
    return json.loads(cleaned)


def _repair_json_syntax_only(client: OpenAI, bad_json: str) -> dict:
    prompt = (
        "Fix this into VALID JSON ONLY.\n"
        "Rules:\n"
        "- Output ONLY a JSON object.\n"
        "- No markdown, no commentary.\n"
        "- Only fix JSON syntax (missing commas/quotes/braces).\n"
        '- If a value is clearly missing, use "N/A".\n'
    )

    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": bad_json},
        ],
        temperature=0.0,
        max_tokens=1200,
    )
    return _try_parse_json(resp.choices[0].message.content)


def _repair_json_to_schema(client: OpenAI, bad_text: str) -> dict:
    schema_prompt = """
Convert the following into VALID JSON ONLY (no markdown, no commentary).
It MUST match this schema exactly (no extra keys):

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
          "materials_required": "string"
        }
      ]
    }
  ]
}

Rules:
- Output ONLY JSON.
- If missing anything, fill with "N/A".
- Keep values concise (1–2 sentences max).
"""

    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": schema_prompt},
            {"role": "user", "content": bad_text},
        ],
        temperature=0.0,
        max_tokens=1200,
    )

    repaired_text = resp.choices[0].message.content

    try:
        return _try_parse_json(repaired_text)
    except Exception:
        return _repair_json_syntax_only(client, repaired_text)


def run_all_agents(input_data: dict) -> dict:
    client = _get_client()

    system_prompt = """
You are a curriculum architect.

Return STRICT JSON ONLY matching this schema:

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
          "materials_required": "string"
        }
      ]
    }
  ]
}

Hard constraints:
- "units" is an array.
- Each unit has "unit_title" and "activities" array.
- Each activity has ALL 8 fields listed above.
- No extra keys.
- Generate EXACTLY input_data["units"] units.
- Generate EXACTLY input_data["activities_per_unit"] activities per unit.
- Keep each field concise (1–2 sentences max).
"""

    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_data)},
        ],
        temperature=0.2,
        max_tokens=1200,
    )

    raw = resp.choices[0].message.content

    try:
        parsed = _try_parse_json(raw)
    except Exception:
        parsed = _repair_json_to_schema(client, raw)

    # Defensive normalization
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

    return parsed
