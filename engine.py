"""
Ghost Engine - Smart Market Scanner

This module performs a lightweight Solana RPC health check.
It does not execute trades.
"""

import requests

from config import RPC_URL


def scan_smart_market():
    """
    Check whether the configured Solana RPC endpoint is reachable.

    Returns:
        dict: RPC health information.
    """
    if not RPC_URL:
        return {
            "ok": False,
            "error": "RPC_URL is not configured",
        }

    try:
        response = requests.post(
            RPC_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth",
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        return {
            "ok": True,
            "status_code": response.status_code,
            "result": data.get("result"),
        }

    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": str(exc),
        }

    except ValueError as exc:
        return {
            "ok": False,
            "error": f"Invalid JSON response: {exc}",
        }


if __name__ == "__main__":
    result = scan_smart_market()
    print("=== RPC HEALTH ===")
    print(result)
