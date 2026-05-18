import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client=Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL="llama-3.3-70b-versatile"

def ask_llm(prompt):

    response=client.chat.completions.create(

        model=MODEL,

        messages=[

            {
                "role":"user",
                "content":prompt
            }

        ]

    )

    return response.choices[0].message.content