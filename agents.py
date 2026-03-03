from openai import OpenAI
import os
import json


def run_all_agents(input_data):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")

    client = OpenAI(api_key=api_key)

    system_prompt = """
    Generate curriculum in STRICT JSON format.

    Required format:

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

    Return ONLY valid JSON.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_data)}
        ],
        temperature=0.3,
        max_tokens=1200
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except Exception as e:
        print("RAW GPT OUTPUT:", content)
        raise ValueError("GPT returned invalid JSON")
