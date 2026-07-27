import requests

DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/search"
REQUEST_TIMEOUT = 10
MIN_LIQUIDITY = 5_000
MAX_PAIRS = 100

session = requests.Session()

session.headers.update({
    "User-Agent": "GhostEngine/1.0",
    "Accept": "application/json",
})


def fetch_pairs():
    """Fetch valid Solana pairs from DexScreener."""

    try:
        response = session.get(
            DEXSCREENER_URL,
            params={"q": "SOL"},
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        pairs = data.get("pairs", [])

        # Solana only
        pairs = [
            pair
            for pair in pairs
            if pair.get("chainId") == "solana"
        ]

        valid_pairs = []

        for pair in pairs:
            token = pair.get("baseToken") or {}
            liquidity = pair.get("liquidity") or {}

            liquidity_usd = liquidity.get("usd") or 0

            if not token.get("address"):
                continue

            if not pair.get("pairAddress"):
                continue

            if liquidity_usd < MIN_LIQUIDITY:
                continue

            valid_pairs.append(pair)

        return valid_pairs[:MAX_PAIRS]

    except requests.RequestException as error:
        print(f"[SCANNER] Network error: {error}")
        return []

    except ValueError as error:
        print(f"[SCANNER] Invalid JSON: {error}")
        return []

    except Exception as error:
        print(f"[SCANNER] Unexpected error: {error}")
        return []


if __name__ == "__main__":
    pairs = fetch_pairs()

    print(f"LIVE SOLANA PAIRS: {len(pairs)}")

    for i, pair in enumerate(pairs[:10]):
        token = pair.get("baseToken") or {}
        liquidity = pair.get("liquidity") or {}

        print(
            f"{i} | "
            f"{token.get('symbol')} | "
            f"{token.get('address')} | "
            f"DEX={pair.get('dexId')} | "
            f"PRICE=${pair.get('priceUsd')} | "
            f"LIQ=${liquidity.get('usd')}"
            )
