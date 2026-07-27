from scanner import fetch_pairs
from filters import filter_pairs
from scorer import score_pair
from logger import save_pairs

pairs = fetch_pairs()

pairs = filter_pairs(pairs)

results = []

for pair in pairs:

    score = score_pair(pair)

    pair["score"] = score

    results.append(pair)

results.sort(key=lambda x: x["score"], reverse=True)

save_pairs(results)

for pair in results[:10]:

    print(
        pair["baseToken"]["symbol"],
        "Score:",
        pair["score"],
        "Price:",
        pair["priceUsd"]
    )
