"""
Smart Wallet Discovery Engine

يكتشف محافظ نشطة من معاملات Solana
باستخدام Helius API
"""

import os
import json
import requests
from collections import Counter


HELIUS_KEY = os.getenv(
    "HELIUS_API_KEY"
)


RPC_URL = (
    "https://mainnet.helius-rpc.com/"
    "?api-key="
    + str(HELIUS_KEY)
)



def get_token_transactions(
    token_address,
    limit=100
):


    payload = {

        "jsonrpc":"2.0",

        "id":"ghost",

        "method":
        "getSignaturesForAddress",

        "params":[

            token_address,

            {
                "limit":limit
            }

        ]

    }


    try:


        r=requests.post(

            RPC_URL,

            json=payload,

            timeout=10

        )


        return r.json().get(
            "result",
            []
        )


    except Exception:


        return []





def get_wallets_from_transactions(
    transactions
):


    wallets = Counter()


    for tx in transactions:


        if "accountKeys" in tx:


            for wallet in tx["accountKeys"]:

                wallets[wallet] += 1



    return wallets





def discover_smart_wallets(
    token_address
):


    txs = get_token_transactions(
        token_address
    )


    wallets = get_wallets_from_transactions(
        txs
    )


    smart = []



    for wallet,count in wallets.items():


        if count >= 3:


            smart.append(

                {

                "address":wallet,

                "activity":count,

                "win_rate":0

                }

            )



    return smart





def save_smart_wallets(
    wallets
):


    with open(
        "smart_wallets.json",
        "w"
    ) as f:


        json.dump(

            wallets,

            f,

            indent=4

        )





if __name__ == "__main__":


    token=input(
        "Token address: "
    )


    wallets = discover_smart_wallets(
        token
    )


    save_smart_wallets(
        wallets
    )


    print(
        "Found:",
        len(wallets),
        "wallets"
  )
