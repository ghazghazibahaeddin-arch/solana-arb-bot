import os
import requests


KEY=os.getenv(
"BIRDEYE_API_KEY"
)


def token_holders(address):


    url=(
    "https://public-api.birdeye.so/"
    "defi/v3/token/holder"
    )


    headers={

    "X-API-KEY":KEY

    }


    params={

    "address":address

    }


    r=requests.get(

        url,

        headers=headers,

        params=params

    )


    return r.json()
