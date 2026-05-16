from services.llm_service import ask_llm

def explain_code(file_path: str):

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    prompt = f"""
    Explain this code simply.

    Code:
    {code[:12000]}
    """

    return ask_llm(prompt)