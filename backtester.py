# backtester.py

import json

def load():

    try:
        with open("tokens.json", "r") as f:
            return json.load(f)

    except:
        return []
