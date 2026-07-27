import json

def save_pairs(data):

    with open("tokens.json", "w") as f:
        json.dump(data, f, indent=4)
