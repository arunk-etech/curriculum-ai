from openai import OpenAI
import os
import json


def run_all_agents(input_data):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables")

    client = OpenAI(api_key=api_key)

    system_prompt = """
    You are an expert curriculum architect.

    Design a structured curriculum based on:
    - Course name
    - Grade
    - Number of units
    - Activities per unit
    - Activity types (if provided)
    - 21st century skill focus
    - Framework alignment (if provided)
    - Rubric expectations (if provided)

    Return structured JSON only.
    Do not return explanation text.
    Keep output concise but structured.
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

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        # If GPT returns non-perfect JSON, return raw content
        return {"raw_output": content}
