"""
Smart Money Tracker

Tracks wallets that historically entered early.
"""

import json

from helius_client import wallet_activity



FILE = "smart_wallets.json"



def load_wallets():

    try:

        with open(FILE,"r") as f:

            return json.load(f)


    except:

        return []




def wallet_score(wallet):


    win_rate = wallet.get(
        "win_rate",
        0
    )


    return min(
        win_rate,
        100
    )




def analyze_wallet_activity(address):


    try:

        data = wallet_activity(
            address
        )


        txs = data.get(
            "result",
            []
        )


        return len(txs)



    except:

        return 0




def smart_wallet_score(pair):


    wallets = load_wallets()


    if not wallets:

        return 0



    score = 0



    for wallet in wallets:


        activity = analyze_wallet_activity(
            wallet["address"]
        )


        if activity > 0:


            score += wallet_score(
                wallet
            ) / len(wallets)



    return min(
        round(score,2),
        100
    )



def analyze(pair):

    return smart_wallet_score(
        pair
      )
