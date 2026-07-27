import json

def load_wallet():

    try:

        with open("wallet.json","r") as f:
            return json.load(f)

    except:

        return {}
