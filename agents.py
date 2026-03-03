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
    # Hard caps to prevent huge outputs (avoids truncation)
    units_target = int(input_data.get("units", 1))
    acts_target = int(input_data.get("activities_per_unit", 1))

    # ✅ cap to keep Railway fast + prevent tool-args truncation
    units_target = min(max(units_target, 1), 4)          # max 4 units
    acts_target = min(max(acts_target, 1), 5)            # max 5 activities each

    input_data = dict(input_data)
    input_data["units"] = units_target
    input_data["activities_per_unit"] = acts_target

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
        f"Generate EXACTLY {units_target} units.\n"
        f"For each unit, generate EXACTLY {acts_target} activities.\n"
        "VERY IMPORTANT OUTPUT LIMITS:\n"
        "- unit_title: max 60 characters\n"
        "- activity_name: max 80 characters\n"
        "- description/objective/outcomes/content_knowledge/skills_21st/sdg_aligned/materials_required:\n"
        "  each max 120 characters (1 short sentence).\n"
        "- Do NOT use newline characters inside any field.\n"
        "Return ONLY by calling submit_curriculum."
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
        max_tokens=1800,  # give enough room so arguments aren't cut mid-string
    )

    msg = resp.choices[0].message
    if not msg.tool_calls:
        raise ValueError("No tool call returned by model")

    args_text = msg.tool_calls[0].function.arguments

    # If truncated, args_text will be invalid JSON; raise to retry
    return json.loads(args_text)


def run_all_agents(input_data: dict) -> dict:
    client = _get_client()

    # Try twice (truncation is intermittent)
    for _ in range(2):
        try:
            parsed = _call_with_tools(client, input_data)
            break
        except Exception:
            time.sleep(0.4)
            parsed = None

    if not parsed:
        raise ValueError("Model output was truncated twice; reduce units/activities.")

    # Defensive normalization
    if not isinstance(parsed, dict):
        parsed = {"units": []}
    if "units" not in parsed or not isinstance(parsed["units"], list):
        parsed["units"] = []

    return parsed
