"""
Ghost Engine - Network Guard

Purpose:
    Detect internet/API availability.

Important:
    This module NEVER executes trades.
"""

import os
import time
from typing import Dict

import requests
from dotenv import load_dotenv


load_dotenv()


REQUEST_TIMEOUT = float(
    os.getenv("NETWORK_TIMEOUT", "8")
)

HEALTH_CACHE_SECONDS = float(
    os.getenv("HEALTH_CACHE_SECONDS", "10")
)


SERVICES = {
    "internet": "https://www.google.com/generate_204",

    "dexscreener": (
        "https://api.dexscreener.com/"
        "token-profiles/latest/v1"
    ),

    "geckoterminal": (
        "https://api.geckoterminal.com/"
        "api/v2/networks/solana/"
        "trending_pools"
    ),

    "helius": (
        "https://api.helius.xyz/v0/"
        "addresses/{address}/transactions"
    ),

    "birdeye": (
        "https://public-api.birdeye.so/"
        "defi/price"
    ),
}


_last_health = {}
_last_health_time = 0.0


def _request(
    url: str,
    headers=None,
    params=None
):

    try:

        response = requests.get(
            url,
            headers=headers or {},
            params=params or {},
            timeout=REQUEST_TIMEOUT
        )

        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "latency_ms": 0,
        }

    except requests.RequestException as exc:

        return {
            "ok": False,
            "status_code": None,
            "error": str(exc),
        }


def check_internet():

    result = _request(
        SERVICES["internet"]
    )

    return bool(
        result.get("ok")
    )


def check_dexscreener():

    result = _request(
        SERVICES["dexscreener"]
    )

    return result


def check_geckoterminal():

    result = _request(
        SERVICES["geckoterminal"]
    )

    return result


def check_helius():

    api_key = os.getenv(
        "HELIUS_API_KEY"
    )

    if not api_key:

        return {
            "ok": False,
            "error": "HELIUS_API_KEY missing"
        }

    # Do not invent a wallet address.
    # We only verify that the Helius host can be reached.
    url = "https://api.helius.xyz"

    return _request(
        url
    )


def check_birdeye():

    api_key = os.getenv(
        "BIRDEYE_API_KEY"
    )

    if not api_key:

        return {
            "ok": False,
            "error": "BIRDEYE_API_KEY missing"
        }

    return _request(
        "https://public-api.birdeye.so",
        headers={
            "X-API-KEY": api_key
        }
    )


def check_all(
    force=False
) -> Dict:

    global _last_health
    global _last_health_time

    now = time.time()

    if (
        not force
        and
        _last_health
        and
        now - _last_health_time
        < HEALTH_CACHE_SECONDS
    ):

        return _last_health

    internet = check_internet()

    if not internet:

        result = {
            "internet": False,
            "healthy": False,
            "reason": "internet_unavailable"
        }

        _last_health = result
        _last_health_time = now

        return result

    dex = check_dexscreener()
    gecko = check_geckoterminal()
    helius = check_helius()
    birdeye = check_birdeye()

    services = {
        "internet": internet,
        "dexscreener": dex,
        "geckoterminal": gecko,
        "helius": helius,
        "birdeye": birdeye,
    }

    healthy = (
        internet
        and dex.get("ok", False)
        and gecko.get("ok", False)
    )

    result = {
        "healthy": healthy,
        "services": services,
        "timestamp": now,
    }

    _last_health = result
    _last_health_time = now

    return result


def network_is_safe():

    status = check_all()

    return bool(
        status.get("healthy")
    )


if __name__ == "__main__":

    import json

    print(
        json.dumps(
            check_all(
                force=True
            ),
            indent=2
        )
)
