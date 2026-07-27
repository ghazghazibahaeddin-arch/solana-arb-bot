import requests


BASE = (
"https://api.geckoterminal.com/api/v2"
)


def get_pool_data(network, pool):

    url = (
    f"{BASE}/networks/"
    f"{network}/pools/{pool}"
    )


    r=requests.get(
        url,
        timeout=10
    )


    return r.json()
