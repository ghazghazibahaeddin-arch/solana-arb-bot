import os
import requests
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("HELIUS_API_KEY")

if not KEY:
    raise RuntimeError(
        "HELIUS_API_KEY غير موجود في .env — "
        "أضف السطر التالي إلى ملف .env في جذر المشروع:\n"
        "HELIUS_API_KEY=your_key_here"
    )

URL = (
    "https://mainnet.helius-rpc.com/"
    "?api-key="
    + KEY
)


def wallet_activity(wallet):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            wallet,
            {
                "limit": 100
            }
        ]
    }
    r = requests.post(
        URL,
        json=payload
    )
    return r.json()
