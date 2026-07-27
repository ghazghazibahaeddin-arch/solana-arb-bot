"""
Ghost Engine Early Buyer Detector

Detects wallets that entered a token early.

Uses:
- Helius transactions
- Token holders
- Timing analysis

Purpose:
Find wallets that often buy before momentum.
"""


import os
import requests
from collections import Counter
from datetime import datetime



HELIUS_API_KEY = os.getenv(
    "HELIUS_API_KEY"
)



HELIUS_TX_URL = (
    "https://api.helius.xyz/v0/"
    "addresses/"
)



def get_transactions(
    address,
    limit=100
):


    url = (

        HELIUS_TX_URL

        +

        address

        +

        "/transactions"

    )


    params = {

        "api-key":
        HELIUS_API_KEY,

        "limit":
        limit

    }


    try:


        r = requests.get(

            url,

            params=params,

            timeout=10

        )


        return r.json()



    except Exception:


        return []




def extract_wallets(
    transactions
):


    wallets = Counter()



    for tx in transactions:


        accounts = tx.get(
            "accountData",
            []
        )


        for acc in accounts:


            wallet = acc.get(
                "account"
            )


            if wallet:

                wallets[wallet]+=1



    return wallets




def analyze_entry_time(
    transactions
):


    early = 0


    total = len(
        transactions
    )



    now = datetime.utcnow()



    for tx in transactions:


        timestamp = tx.get(
            "timestamp"
        )


        if not timestamp:

            continue



        tx_time = datetime.fromtimestamp(
            timestamp
        )


        age = (
            now - tx_time
        ).total_seconds()



        # دخل خلال أول ساعة من النشاط

        if age < 3600:

            early += 1



    if total == 0:

        return 0



    return round(

        (early / total) * 100,

        2

    )




def detect_early_buyers(
    token_address
):


    transactions = get_transactions(
        token_address
    )



    wallets = extract_wallets(
        transactions
    )



    results = []



    for wallet,count in wallets.items():


        timing_score = analyze_entry_time(
            transactions
        )



        if count >= 2:


            results.append(

                {

                "wallet":
                wallet,


                "transactions":
                count,


                "early_score":
                timing_score

                }

            )



    results.sort(

        key=lambda x:
        x["early_score"],

        reverse=True

    )



    return results[:20]





if __name__ == "__main__":


    token=input(
        "Token address: "
    )


    buyers = detect_early_buyers(
        token
    )


    for buyer in buyers:

        print(
            buyer
      )
