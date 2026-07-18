from services.llm_service import ask_llm

def rewrite_code(code, instructions="Refactor this code to be cleaner and more efficient."):
    """
    Rewrites code based on provided instructions.
    """
    prompt = f"""
Input Code:
```
{code}
```

Instructions: {instructions}

Please rewrite the code according to the instructions. Provide only the code in your response, without any explanations or markdown blocks.
"""
    return ask_llm(prompt)

def remove_dead_code(code):
    """
    Specific helper to remove dead code.
    """
    return rewrite_code(code, "Identify and remove any dead code, unused variables, or unreachable logic from this code.")
