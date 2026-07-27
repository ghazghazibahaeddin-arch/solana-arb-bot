import requests
from config import DEX_API

def fetch_pairs():
    try:
        response = requests.get(DEX_API, timeout=10)
        response.raise_for_status()

        data = response.json()

        return data.get("pairs", [])

    except Exception as e:
        print("Scanner Error:", e)
        return []
