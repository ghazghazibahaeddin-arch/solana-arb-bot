import requests


def get_tokens():

    url = (
    "https://api.dexscreener.com/"
    "latest/dex/search?q=SOL"
    )

    r = requests.get(
        url,
        timeout=10
    )

    data = r.json()

    return data.get(
        "pairs",
        []
    )
