from openai import OpenAI
import os
import json


def run_all_agents(input_data):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")

    client = OpenAI(api_key=api_key)

    system_prompt = """
    You are an expert curriculum architect.

    Return curriculum in STRICT JSON format:

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

    Return JSON only. No explanation.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_data)}
        ],
        temperature=0.3,
        max_tokens=1200
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("GPT did not return valid JSON")
