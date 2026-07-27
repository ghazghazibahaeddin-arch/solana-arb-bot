import requests

class DexScreenerScanner:
    """
    Integrates DexScreener Public API to scan newly launched pairs 
    and high-velocity liquidity pools on Solana and other networks.
    """
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest/dex/tokens/"
        
    def fetch_token_market_data(self, token_address):
        try:
            url = f"{self.base_url}{token_address}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])
                if pairs:
                    best_pair = pairs[0] # Select highest liquidity pair
                    return {
                        "status": "SUCCESS",
                        "dex": best_pair.get("dexId"),
                        "price_usd": float(best_pair.get("priceUsd", 0)),
                        "liquidity": best_pair.get("liquidity", {}).get("usd", 0),
                        "volume_h24": best_pair.get("volume", {}).get("h24", 0)
                    }
        except Exception:
            pass
        return {"status": "ERROR", "liquidity": 0}

if __name__ == "__main__":
    scanner = DexScreenerScanner()
    # Test with Solana token mint address example (e.g., USDC on Solana)
    result = scanner.fetch_token_market_data("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    print("DexScreener Scan Result:", result)
                  
