"""
Ghost Engine - Live Scanner

Source:
    DexScreener public API

The scanner:
    1. Fetches real Solana market data.
    2. Normalizes the response.
    3. Removes obviously incomplete pairs.
    4. Saves historical snapshots.
"""

import time
import requests

from database import (
    save_snapshot,
    count_snapshots
)


DEXSCREENER_URL = (
    "https://api.dexscreener.com/"
    "latest/dex/search"
)

REQUEST_TIMEOUT = 10

MIN_LIQUIDITY = 5_000

MAX_PAIRS = 100


session = requests.Session()

session.headers.update(
    {
        "User-Agent":
        "GhostEngine/1.0"
    }
)


def fetch_pairs():
    """
    Fetch real Solana pairs.

    DexScreener search endpoint is used because it
    returns pair-level market information.
    """

    try:

        response = session.get(
            DEXSCREENER_URL,
            params={
                "q": "SOL"
            },
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        pairs = data.get(
            "pairs",
            []
        )

        # Only Solana
        pairs = [
            pair
            for pair in pairs
            if pair.get("chainId")
            == "solana"
        ]

        return pairs[:MAX_PAIRS]

    except requests.RequestException as error:

        print(
            f"[SCANNER] Network error: {error}"
        )

        return []

    except ValueError as error:

        print(
            f"[SCANNER] Invalid JSON: {error}"
        )

        return []

    except Exception as error:

        print(
            f"[SCANNER] Unexpected error: {error}"
        )

        return []


def normalize_pair(pair):
    """
    Ensure fields expected by other Ghost Engine
    modules exist.
    """

    pair.setdefault(
        "liquidity",
        {}
    )

    pair.setdefault(
        "volume",
        {}
    )

    pair.setdefault(
        "txns",
        {}
    )

    pair.setdefault(
        "baseToken",
        {}
    )

    pair.setdefault(
        "priceUsd",
        "0"
    )

    pair.setdefault(
        "marketCap",
        0
    )

    pair.setdefault(
        "fdv",
        0
    )

    return pair


def is_valid_pair(pair):
    """Reject incomplete or unusable market data."""

    if pair.get("chainId") != "solana":
        return False

    base = pair.get(
        "baseToken",
        {}
    )

    address = base.get(
        "address"
    )

    if not address:
        return False

    try:

        price = float(
            pair.get(
                "priceUsd",
                0
            ) or 0
        )

    except (
        TypeError,
        ValueError
    ):

        price = 0

    liquidity = pair.get(
        "liquidity",
        {}
    ) or {}

    try:

        liquidity_usd = float(
            liquidity.get(
                "usd",
                0
            ) or 0
        )

    except (
        TypeError,
        ValueError
    ):

        liquidity_usd = 0

    if price <= 0:
        return False

    if liquidity_usd < MIN_LIQUIDITY:
        return False

    return True


def scan_once(
    save=True
):
    """
    One live scan.

    Returns real pairs obtained from DexScreener.
    """

    raw_pairs = fetch_pairs()

    valid_pairs = []

    for pair in raw_pairs:

        pair = normalize_pair(
            pair
        )

        if not is_valid_pair(
            pair
        ):
            continue

        valid_pairs.append(
            pair
        )

        if save:

            # Save exactly what was observed.
            save_snapshot(
                pair=pair,
                score=0,
                risk=0,
                holders=0,
                timestamp=time.time()
            )

    return valid_pairs


def get_live_market():
    """Compatibility alias."""

    return scan_once(
        save=True
    )


def run_forever(
    interval=3
):
    """
    Continuously collect real market snapshots.

    This is DATA COLLECTION only.
    It does not trade.
    """

    print(
        "Ghost Engine live scanner started."
    )

    print(
        f"Scanning every {interval} seconds."
    )

    while True:

        started = time.time()

        pairs = scan_once(
            save=True
        )

        print(
            f"[SCANNER] "
            f"{len(pairs)} valid Solana pairs | "
            f"history={count_snapshots()}"
        )

        elapsed = (
            time.time()
            - started
        )

        sleep_for = max(
            0,
            interval - elapsed
        )

        time.sleep(
            sleep_for
        )


if __name__ == "__main__":

    run_forever(
        interval=3
        )
