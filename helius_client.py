import os
import requests


KEY=os.getenv(
"5ee01e91-4efc-43b0-81f3-2b81d2ea7437"
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
