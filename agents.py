from openai import OpenAI
import os
import json

def call_gpt(system_prompt, user_input):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables")

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_input)}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content


def run_all_agents(input_data):
    curriculum = call_gpt("You are Curriculum Designer. Return structured JSON.", input_data)
    research = call_gpt("You are Research Analyst. Return structured JSON.", curriculum)

    return {
        "curriculum": curriculum,
        "research": research
    }
