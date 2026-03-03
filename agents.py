from openai import OpenAI
import os


def run_all_agents(input_data):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-4o-mini",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "curriculum_schema",
                "schema": {
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
                                                "activity_title": {"type": "string"},
                                                "objective": {"type": "string"},
                                                "21st_century_skill": {"type": "string"},
                                                "assessment": {"type": "string"}
                                            },
                                            "required": [
                                                "activity_title",
                                                "objective",
                                                "21st_century_skill",
                                                "assessment"
                                            ]
                                        }
                                    }
                                },
                                "required": ["unit_title", "activities"]
                            }
                        }
                    },
                    "required": ["units"]
                }
            }
        },
        input=[
            {
                "role": "system",
                "content": "Generate curriculum based on the user input."
            },
            {
                "role": "user",
                "content": str(input_data)
            }
        ],
        temperature=0.3,
    )

    return response.output_parsed
