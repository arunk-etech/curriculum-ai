from openai import OpenAI
import os
import json
import time

MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")
    return OpenAI(api_key=api_key)


def _call_with_tools(client: OpenAI, input_data: dict) -> dict:
    """
    Uses function calling so the model returns structured JSON arguments.
    This avoids brittle 'JSON in text' parsing.
    """
    tool_schema = {
        "type": "function",
        "function": {
            "name": "submit_curriculum",
            "description": "Return the curriculum in a strict structured format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "units": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "unit_title": {"type": "string"},
                                "activities": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "activity_name": {"type": "string"},
                                            "description": {"type": "string"},
                                            "objective": {"type": "string"},
                                            "outcomes": {"type": "string"},
                                            "content_knowledge": {"type": "string"},
                                            "skills_21st": {"type": "string"},
                                            "sdg_aligned": {"type": "string"},
                                            "materials_required": {"type": "string"},
                                        },
                                        "required": [
                                            "activity_name",
                                            "description",
                                            "objective",
                                            "outcomes",
                                            "content_knowledge",
                                            "skills_21st",
                                            "sdg_aligned",
                                            "materials_required",
                                        ],
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            "required": ["unit_title", "activities"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["units"],
                "additionalProperties": False,
            },
        },
    }

    system_prompt = (
        "You are a curriculum architect.\n"
        "Generate EXACTLY input_data['units'] units.\n"
        "For each unit, generate EXACTLY input_data['activities_per_unit'] activities.\n"
        "Keep every field concise (1–2 sentences).\n"
        "Return ONLY by calling the function submit_curriculum."
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_data)},
        ],
        tools=[tool_schema],
        tool_choice={"type": "function", "function": {"name": "submit_curriculum"}},
        temperature=0.2,
        max_tokens=1200,
    )

    msg = resp.choices[0].message
    if not msg.tool_calls:
        # Rare fallback: if tool call not returned, raise to retry
        raise ValueError("No tool call returned by model")

    args_text = msg.tool_calls[0].function.arguments
    return json.loads(args_text)


def run_all_agents(input_data: dict) -> dict:
    client = _get_client()

    # 1) Try once
    try:
        parsed = _call_with_tools(client, input_data)
    except Exception:
        # 2) Retry once (short backoff)
        time.sleep(0.5)
        parsed = _call_with_tools(client, input_data)

    # Defensive normalization (so sheets never crashes)
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
