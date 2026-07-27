"""
Ghost Engine Scanner

Source:
DexScreener API

وظيفته:
- جلب أزواج Solana الحية
- تحديث البيانات كل عدة ثواني
"""

import requests
import time


DEXSCREENER_URL = (
    "https://api.dexscreener.com/"
    "latest/dex/search?q=SOL"
)



def fetch_pairs():

    try:

        response = requests.get(
            DEXSCREENER_URL,
            timeout=10
        )


        response.raise_for_status()


        data = response.json()


        pairs = data.get(
            "pairs",
            []
        )


        # فقط Solana

        sol_pairs = [

            pair

            for pair in pairs

            if pair.get(
                "chainId"
            ) == "solana"

        ]


        return sol_pairs



    except Exception as e:


        print(
            "Scanner error:",
            e
        )


        return []




def live_scanner(
        interval=2
):

    """
    Scanner loop

    كل interval ثانية
    يجلب بيانات جديدة
    """

    while True:


        print(
            "Scanning Solana..."
        )


        pairs = fetch_pairs()



        if pairs:


            yield pairs


        else:

            print(
                "No pairs found"
            )


        time.sleep(
            interval
        )
