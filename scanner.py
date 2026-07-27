import requests
import time


DEX_URL = "https://api.dexscreener.com/latest/dex/search?q=SOL"


def fetch_pairs():

    try:

        response = requests.get(
            DEX_URL,
            timeout=10
        )

        data = response.json()

        return data.get("pairs", [])


    except Exception as e:

        print("Scanner error:", e)

        return []



def live_scanner(interval=2):

    """
    يفحص السوق كل ثانيتين
    """

    while True:

        pairs = fetch_pairs()

        print(
            "Scanned:",
            len(pairs),
            "tokens"
        )


        yield pairs


        time.sleep(interval)
