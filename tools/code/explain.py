from services.llm_service import ask_llm

def explain_code(code):

    prompt=f"""

Explain this code simply.

{code}

"""

    return ask_llm(prompt)