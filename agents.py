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


# -------------------- Agent 1: Curriculum (2-step) --------------------

def _agent1_curriculum(client: OpenAI, input_data: dict) -> dict:
    units_target = int(input_data.get("units", 1))
    acts_target = int(input_data.get("activities_per_unit", 1))

    # Step 1: Outline
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

    # Step 2: Details
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
            "Use 21st century skill focus/frameworks/rubric instructions if present.\n"
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
            max_tokens=1800,
        )

        acts = list(details.get("activities") or [])
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
        for i in range(min(len(acts), len(activity_names))):
            acts[i]["activity_name"] = activity_names[i]

        final_units.append({"unit_title": unit_title, "activities": acts})

    return {"units": final_units}


# -------------------- Agent 2–5 schemas --------------------

def _citations_schema():
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"},
                "note": {"type": "string"},
            },
            "required": ["title", "url"],
            "additionalProperties": False,
        }
    }


def _agent2_research(client: OpenAI, payload: dict) -> dict:
    tool = {
        "type": "function",
        "function": {
            "name": "submit_research",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "unit_rationales": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "unit_no": {"type": "integer"},
                                "unit_title": {"type": "string"},
                                "why_this_sequence": {"type": "string"},
                                "pedagogy": {"type": "string"},
                                "cognitive_principle": {"type": "string"},
                            },
                            "required": ["unit_no", "unit_title", "why_this_sequence"],
                            "additionalProperties": False
                        }
                    },
                    "citations": _citations_schema(),
                },
                "required": ["summary", "unit_rationales", "citations"],
                "additionalProperties": False,
            }
        }
    }

    system = (
        "You are an education research analyst.\n"
        "Explain the curriculum design rationale (sequencing, pedagogy, cognitive science).\n"
        "Citations: include 3–6 references with URLs.\n"
        "Keep answers concise.\n"
        "Return only via tool call."
    )

    return _tool_call(client, system, payload, tool, "submit_research", max_tokens=1400)


def _agent3_govt_alignment(client: OpenAI, payload: dict) -> dict:
    tool = {
        "type": "function",
        "function": {
            "name": "submit_govt_alignment",
            "parameters": {
                "type": "object",
                "properties": {
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "unit_no": {"type": "integer"},
                                "activity_no": {"type": "integer"},
                                "alignment": {"type": "string"},
                                "standard_reference": {"type": "string"},
                            },
                            "required": ["unit_no", "activity_no", "alignment"],
                            "additionalProperties": False
                        }
                    },
                    "citations": _citations_schema(),
                },
                "required": ["rows", "citations"],
                "additionalProperties": False
            }
        }
    }

    system = (
        "You align the curriculum with NCERT/SCERT/NEP 2020 at a high level.\n"
        "Provide mapping rows per activity (unit_no, activity_no).\n"
        "Citations: include 3–6 official references with URLs.\n"
        "Return only via tool call."
    )

    return _tool_call(client, system, payload, tool, "submit_govt_alignment", max_tokens=1600)


def _agent4_international_alignment(client: OpenAI, payload: dict) -> dict:
    tool = {
        "type": "function",
        "function": {
            "name": "submit_international_alignment",
            "parameters": {
                "type": "object",
                "properties": {
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "unit_no": {"type": "integer"},
                                "activity_no": {"type": "integer"},
                                "unicef_life_skill": {"type": "string"},
                                "skills_builder_skill": {"type": "string"},
                                "sdg": {"type": "string"},
                            },
                            "required": ["unit_no", "activity_no"],
                            "additionalProperties": False
                        }
                    },
                    "citations": _citations_schema(),
                },
                "required": ["rows", "citations"],
                "additionalProperties": False
            }
        }
    }

    system = (
        "You align the curriculum with UNICEF Life Skills + Skills Builder + SDGs.\n"
        "Provide mapping rows per activity (unit_no, activity_no).\n"
        "Citations: include 3–6 framework references with URLs.\n"
        "Return only via tool call."
    )

    return _tool_call(client, system, payload, tool, "submit_international_alignment", max_tokens=1600)


def _agent5_studies(client: OpenAI, payload: dict) -> dict:
    tool = {
        "type": "function",
        "function": {
            "name": "submit_studies",
            "parameters": {
                "type": "object",
                "properties": {
                    "studies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "what_it_says": {"type": "string"},
                                "age_grade": {"type": "string"},
                                "how_to_use_in_class": {"type": "string"},
                                "url": {"type": "string"},
                            },
                            "required": ["topic", "what_it_says", "url"],
                            "additionalProperties": False
                        }
                    },
                    "citations": _citations_schema(),
                },
                "required": ["studies", "citations"],
                "additionalProperties": False
            }
        }
    }

    system = (
        "You provide research studies relevant to this curriculum and skill focus.\n"
        "Return 4–8 studies with links.\n"
        "Citations: include same or extra references with URLs.\n"
        "Return only via tool call."
    )

    return _tool_call(client, system, payload, tool, "submit_studies", max_tokens=1600)


# -------------------- Orchestrator --------------------

def run_all_agents(input_data: dict) -> dict:
    client = _client()

    curriculum = _agent1_curriculum(client, input_data)

    # Make a compact payload for other agents to reduce token use
    compact = {
        "course_name": input_data.get("course_name"),
        "grade": input_data.get("grade"),
        "skill_focus_21st": input_data.get("skill_focus_21st"),
        "frameworks": input_data.get("frameworks"),
        "rubric_description": input_data.get("rubric_description"),
        "special_instructions": input_data.get("special_instructions"),
        # send only titles + activity names to alignment agents
        "outline": [
            {
                "unit_no": i + 1,
                "unit_title": u.get("unit_title", "N/A"),
                "activities": [
                    {"activity_no": j + 1, "activity_name": a.get("activity_name", "N/A")}
                    for j, a in enumerate(u.get("activities", []))
                ],
            }
            for i, u in enumerate(curriculum.get("units", []))
        ]
    }

    research = _agent2_research(client, compact)
    govt = _agent3_govt_alignment(client, compact)
    intl = _agent4_international_alignment(client, compact)
    studies = _agent5_studies(client, compact)

    return {
        "curriculum": curriculum,
        "research": research,
        "govt_alignment": govt,
        "international_alignment": intl,
        "studies": studies,
    }
