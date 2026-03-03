from openai import OpenAI
import os
import json

MODEL = "gpt-4o-mini"


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")
    return OpenAI(api_key=api_key)


def _tool_call(client: OpenAI, system_prompt: str, user_payload: dict, tool_schema: dict, tool_name: str, max_tokens: int):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)}
        ],
        tools=[tool_schema],
        tool_choice={"type": "function", "function": {"name": tool_name}},
        temperature=0.2,
        max_tokens=max_tokens,
    )

    msg = resp.choices[0].message
    if not msg.tool_calls:
        raise ValueError("No tool call returned by model")

    args_text = msg.tool_calls[0].function.arguments
    return json.loads(args_text)


def run_all_agents(input_data: dict) -> dict:
    """
    Two-step generation:
    1) Outline: unit titles + activity names
    2) Details: for each unit, generate details for exactly activities_per_unit activities
    """
    client = _client()

    units_target = int(input_data.get("units", 1))
    acts_target = int(input_data.get("activities_per_unit", 1))

    # ---- STEP 1: OUTLINE (small output) ----
    outline_tool = {
        "type": "function",
        "function": {
            "name": "submit_outline",
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
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["unit_title", "activities"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["units"],
                "additionalProperties": False
            }
        }
    }

    outline_system = (
        "You are a curriculum architect.\n"
        f"Generate EXACTLY {units_target} units.\n"
        f"For each unit, generate EXACTLY {acts_target} activity names.\n"
        "Return only via the tool call.\n"
        "Keep titles short.\n"
    )

    outline = _tool_call(
        client=client,
        system_prompt=outline_system,
        user_payload=input_data,
        tool_schema=outline_tool,
        tool_name="submit_outline",
        max_tokens=800
    )

    # Defensive trimming
    outline_units = outline.get("units", [])[:units_target]
    for u in outline_units:
        u["activities"] = (u.get("activities") or [])[:acts_target]

    # ---- STEP 2: DETAILS PER UNIT (small per-call output) ----
    detail_tool = {
        "type": "function",
        "function": {
            "name": "submit_unit_details",
            "parameters": {
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
                                "materials_required": {"type": "string"}
                            },
                            "required": [
                                "activity_name",
                                "description",
                                "objective",
                                "outcomes",
                                "content_knowledge",
                                "skills_21st",
                                "sdg_aligned",
                                "materials_required"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["unit_title", "activities"],
                "additionalProperties": False
            }
        }
    }

    final_units = []

    for unit in outline_units:
        unit_title = unit.get("unit_title", "N/A")
        activity_names = unit.get("activities", [])

        detail_system = (
            "You are a curriculum architect.\n"
            f"Create details for EXACTLY {acts_target} activities.\n"
            "Description must be 4–5 lines (line breaks allowed).\n"
            "Keep other fields concise (1–2 sentences).\n"
            "Use the provided 21st century skill focus/frameworks/rubric instructions if present.\n"
            "Return only via the tool call.\n"
        )

        payload = dict(input_data)
        payload["unit_title"] = unit_title
        payload["activity_names"] = activity_names

        # Add a strong hint to use these names
        payload["_instructions"] = {
            "use_these_activity_names_in_order": activity_names
        }

        details = _tool_call(
            client=client,
            system_prompt=detail_system,
            user_payload=payload,
            tool_schema=detail_tool,
            tool_name="submit_unit_details",
            max_tokens=1400
        )

        # Force correct count & names (if model drifts)
        acts = (details.get("activities") or [])[:acts_target]
        for i in range(min(len(acts), len(activity_names))):
            acts[i]["activity_name"] = activity_names[i]

        final_units.append({
            "unit_title": unit_title,
            "activities": acts
        })

    return {"units": final_units}
