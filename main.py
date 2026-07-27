from scanner import fetch_pairs
from filters import filter_pairs
from scorer import score_pair
from logger import save_pairs

from risk_engine import check
from simulator import simulate
from smart_money import analyze
from whale_detector import detect

pairs = fetch_pairs()

pairs = filter_pairs(pairs)

results = []

for pair in pairs:

    if not check(pair):
        continue

    pair["score"] = score_pair(pair)
    pair["simulation"] = simulate(pair)
    pair["smart_money"] = analyze(pair)
    pair["whale"] = detect(pair)

    results.append(pair)

results.sort(key=lambda x: x["score"], reverse=True)

save_pairs(results)

for pair in results[:10]:

    print("=" * 50)
    print("Token :", pair["baseToken"]["symbol"])
    print("Score :", pair["score"])
    print("Price :", pair["priceUsd"])
    print("Liquidity :", pair["liquidity"]["usd"])
    print("Volume :", pair["volume"]["h24"])
    print("Smart Money :", pair["smart_money"])
    print("Whale :", pair["whale"])
    print("Simulation :", pair["simulation"])
