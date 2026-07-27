import os
import requests


API_KEY = os.getenv("SOLSCAN_API_KEY")


BASE_URL = "https://pro-api.solscan.io/v2.0"



def get_token_holders(token_address):

    url = f"{BASE_URL}/token/holders"


    headers = {
        "token": API_KEY
    }


    params = {
        "address": token_address
    }


    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )


    return response.json()
