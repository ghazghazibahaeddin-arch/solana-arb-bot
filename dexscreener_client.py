import requests

DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/search"
TIMEOUT = 10


def search_pairs(query="SOL"):
    try:
        response = requests.get(
            DEXSCREENER_URL,
            params={"q": query},
            headers={"User-Agent": "GhostEngine/1.0"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        pairs = data.get("pairs", [])

        # نحتفظ فقط بأزواج Solana
        solana_pairs = [
            pair for pair in pairs
            if pair.get("chainId") == "solana"
        ]

        return solana_pairs

    except requests.RequestException as error:
        print(f"[DEXSCREENER] Network error: {error}")
        return []

    except ValueError as error:
        print(f"[DEXSCREENER] Invalid JSON: {error}")
        return []


if __name__ == "__main__":
    pairs = search_pairs()

    print(f"Solana pairs found: {len(pairs)}")

    for i, pair in enumerate(pairs[:10]):
        token = pair.get("baseToken", {})
        liquidity = pair.get("liquidity") or {}

        print(
            i,
            "|",
            token.get("symbol"),
            "| price:", pair.get("priceUsd"),
            "| liquidity:", liquidity.get("usd"),
            "| dex:", pair.get("dexId"),
        )
