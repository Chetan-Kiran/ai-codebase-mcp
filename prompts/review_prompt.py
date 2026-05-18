def review_prompt(code):

    return f"""
Review this code.

Find:

1 Bugs
2 Security issues
3 Bad practices
4 Performance issues
5 Suggested improvements

CODE:

{code}
"""