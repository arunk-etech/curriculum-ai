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
    client = _client()

    units_target = int(input_data.get("units", 1))
    acts_target = int(input_data.get("activities_per_unit", 1))

    # ---- STEP 1: OUTLINE ----
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
                                "activities": {"type": "array", "items": {"type": "string"}},
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

    outline_system = (
        "You are a curriculum architect.\n"
        f"Generate EXACTLY {units_target} units.\n"
        f"For each unit, generate EXACTLY {acts_target} activity names.\n"
        "Return only via tool call.\n"
        "Keep titles short.\n"
    )

    outline = _tool_call(
        client=client,
        system_prompt=outline_system,
        user_payload=input_data,
        tool_schema=outline_tool,
        tool_name="submit_outline",
        max_tokens=900,
    )

    outline_units = (outline.get("units") or [])[:units_target]

    # Ensure every unit has exactly acts_target names
    for ui, u in enumerate(outline_units, start=1):
        names = list(u.get("activities") or [])
        names = [str(x).strip() for x in names if str(x).strip()]
        while len(names) < acts_target:
            names.append(f"Activity {len(names)+1} (Unit {ui})")
        u["activities"] = names[:acts_target]
        if not str(u.get("unit_title", "")).strip():
            u["unit_title"] = f"Unit {ui}"

    # ---- STEP 2: DETAILS PER UNIT ----
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
        },
    }

    final_units = []

    for unit in outline_units:
        unit_title = unit.get("unit_title", "N/A")
        activity_names = unit.get("activities", [])

        detail_system = (
            "You are a curriculum architect.\n"
            f"Create details for EXACTLY {acts_target} activities.\n"
            "Description must be 4–5 lines.\n"
            "Keep other fields concise (1–2 sentences).\n"
            "Use the provided 21st century skill focus/frameworks/rubric instructions if present.\n"
            "Return only via tool call.\n"
        )

        payload = dict(input_data)
        payload["unit_title"] = unit_title
        payload["activity_names"] = activity_names
        payload["_instructions"] = {"use_these_activity_names_in_order": activity_names}

        details = _tool_call(
            client=client,
            system_prompt=detail_system,
            user_payload=payload,
            tool_schema=detail_tool,
            tool_name="submit_unit_details",
            max_tokens=1600,
        )

        acts = list(details.get("activities") or [])
        # Force correct count: pad missing activities if model returned fewer
        while len(acts) < acts_target:
            missing_name = activity_names[len(acts)] if len(acts) < len(activity_names) else f"Activity {len(acts)+1}"
            acts.append({
                "activity_name": missing_name,
                "description": "N/A",
                "objective": "N/A",
                "outcomes": "N/A",
                "content_knowledge": "N/A",
                "skills_21st": input_data.get("skill_focus_21st", "N/A") or "N/A",
                "sdg_aligned": "N/A",
                "materials_required": "N/A",
            })

        acts = acts[:acts_target]

        # Force names in order
        for i in range(min(len(acts), len(activity_names))):
            acts[i]["activity_name"] = activity_names[i]

        final_units.append({"unit_title": unit_title, "activities": acts})

    return {"units": final_units}
