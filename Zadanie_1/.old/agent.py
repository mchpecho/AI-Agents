#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types


def calculate(expression: str) -> str:
    """Mini-kalkulačka pre + - * / ( ) a desatinné čísla."""
    allowed = set("0123456789+-*/(). ")
    if any(ch not in allowed for ch in expression):
        raise ValueError("Výraz obsahuje nepovolené znaky.")
    # Pre cvičenie OK (whitelist znakov + bez builtins). V produkcii radšej parser.
    return str(eval(expression, {"__builtins__": {}}, {}))


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("Chýba GEMINI_API_KEY (alebo GOOGLE_API_KEY) v prostredí / .env.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")  # lacnejší variant :contentReference[oaicite:1]{index=1}

    # Krátky prompt = menej tokenov
    user_prompt = " ".join(sys.argv[1:]).strip() or "Vypočítaj (1250*0.18)+(399/3)."
    prompt = (
        "Ak treba výpočet, zavolaj funkciu calculate(expression). "
        f"Otázka: {user_prompt}"
    )

    client = genai.Client(api_key=api_key)

    # 1) Definícia nástroja (function declaration)
    func = types.FunctionDeclaration(
        name="calculate",
        description="Vypočíta aritmetický výraz.",
        parameters_json_schema={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    )
    tool = types.Tool(function_declarations=[func])

    # 2) Prvé volanie LLM (model vráti function_call)
    r1 = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,          # stabilnejšie + menej “ukecanosti”
            tools=[tool],
        ),
    )

    # Ak by model nástroj nepoužil, len vypíšeme text (zriedkavé, ale safe)
    if not r1.function_calls:
        print(r1.text)
        return

    call = r1.function_calls[0]
    args = call.function_call.args  # dict

    # 3) Vykonanie nástroja
    try:
        result = calculate(**args)
        tool_payload = {"result": result}
    except Exception as e:
        tool_payload = {"error": str(e)}

    # 4) Poslanie tool response späť do LLM a získanie finálnej odpovede
    user_content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    function_call_content = r1.candidates[0].content
    function_response_part = types.Part.from_function_response(
        name=call.name,
        response=tool_payload,
    )
    tool_content = types.Content(role="tool", parts=[function_response_part])

    r2 = client.models.generate_content(
        model=model_name,
        contents=[user_content, function_call_content, tool_content],
        config=types.GenerateContentConfig(temperature=0, tools=[tool]),
    )

    print(r2.text)


if __name__ == "__main__":
    main()
