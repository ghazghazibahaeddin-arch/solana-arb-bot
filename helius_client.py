import os
import requests


KEY=os.getenv(
"HELIUS_API_KEY"
)


URL=(
"https://mainnet.helius-rpc.com/"
"?api-key="
+KEY
)


def wallet_activity(wallet):


    payload={

    "jsonrpc":"2.0",
    "id":1,
    "method":
    "getSignaturesForAddress",

    "params":[
        wallet,
        {
        "limit":100
        }
    ]

    }


    r=requests.post(
        URL,
        json=payload
    )


    return r.json()
