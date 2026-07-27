"""
Ghost Engine Wallet Performance Analyzer

Analyzes wallets:
- activity
- early entries
- repeated winners
- performance score

Data source:
Helius API
"""

import os
import json
import requests
from datetime import datetime


HELIUS_API_KEY = os.getenv(
    "HELIUS_API_KEY"
)


HELIUS_URL = (
    "https://api.helius.xyz/v0/"
    "addresses/"
)


SMART_FILE = "smart_wallets.json"



def get_wallet_transactions(wallet, limit=100):

    url = (
        HELIUS_URL
        +
        wallet
        +
        "/transactions"
    )


    params = {

        "api-key": HELIUS_API_KEY,

        "limit": limit

    }


    try:

        response = requests.get(

            url,

            params=params,

            timeout=10

        )


        return response.json()


    except Exception:


        return []




def analyze_wallet(wallet):


    transactions = get_wallet_transactions(
        wallet
    )


    if not transactions:

        return {

            "address": wallet,

            "activity":0,

            "early_entries":0,

            "performance_score":0

        }



    activity = len(
        transactions
    )


    early_entries = 0


    swaps = 0



    for tx in transactions:


        tx_type = tx.get(
            "type",
            ""
        )


        if tx_type in [

            "SWAP",

            "TRANSFER"

        ]:


            swaps += 1



        # المعاملات الحديثة جدًا
        # تعتبر نشاطًا مبكرًا

        timestamp = tx.get(
            "timestamp"
        )


        if timestamp:


            age_days = (

                datetime.utcnow()
                -
                datetime.fromtimestamp(
                    timestamp
                )

            ).days



            if age_days < 7:

                early_entries += 1





    activity_score = min(

        activity,

        100

    )



    early_score = min(

        early_entries * 10,

        100

    )



    swap_score = min(

        swaps,

        100

    )



    final_score = (

        activity_score * 0.4

        +

        early_score * 0.3

        +

        swap_score * 0.3

    )



    return {


        "address": wallet,


        "activity": activity,


        "early_entries": early_entries,


        "swaps": swaps,


        "performance_score":
        round(
            final_score,
            2
        )

    }




def update_smart_wallets():


    try:

        with open(
            SMART_FILE,
            "r"
        ) as f:

            wallets=json.load(f)


    except:


        wallets=[]



    updated=[]



    for wallet in wallets:


        result = analyze_wallet(

            wallet["address"]

        )


        updated.append(

            result

        )



    with open(
        SMART_FILE,
        "w"
    ) as f:


        json.dump(

            updated,

            f,

            indent=4

        )



    return updated




if __name__ == "__main__":


    data = update_smart_wallets()


    for wallet in data:

        print(
            wallet
      )
