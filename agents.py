from openai import OpenAI
import os


def run_all_agents(input_data):

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = """
    You are an expert curriculum architect.

    Generate structured curriculum in this JSON format:

    {
        "course_name": "",
        "grade": "",
        "units": [
            {
                "unit_title": "",
                "activities": [
                    {
                        "activity_title": "",
                        "objective": "",
                        "21st_century_skill": "",
                        "assessment": ""
                    }
                ]
            }
        ]
    }

    Return JSON only.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(input_data)}
        ],
        temperature=0.4,
        max_tokens=1500
    )

    return eval(response.choices[0].message.content)
