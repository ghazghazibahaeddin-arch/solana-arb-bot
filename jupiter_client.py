import requests



def quote(
input_token,
output_token,
amount
):


    url=(
    "https://quote-api.jup.ag/v6/quote"
    )


    params={

    "inputMint":input_token,

    "outputMint":output_token,

    "amount":amount

    }


    r=requests.get(
        url,
        params=params
    )


    return r.json()
