import os
import requests


GROQ_KEY = os.getenv("GROQ_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")



def analyze_token(data):


    prompt=f"""

Analyze this Solana token.

Give only:

RISK: LOW/MEDIUM/HIGH

OPPORTUNITY: YES/NO


DATA:

{data}

"""



    results=[]



    # Groq

    try:

        r=requests.post(

        "https://api.groq.com/openai/v1/chat/completions",

        headers={
        "Authorization":
        f"Bearer {GROQ_KEY}"
        },

        json={

        "model":
        "llama-3.1-8b-instant",

        "messages":[
        {
        "role":"user",
        "content":prompt
        }
        ]

        }

        )


        results.append(
            "Groq:"+r.json()
            ["choices"][0]
            ["message"]
            ["content"]
        )


    except Exception as e:

        results.append(
            "Groq failed"
        )




    # Gemini هنا يضاف بنفس الطريقة


    return results
