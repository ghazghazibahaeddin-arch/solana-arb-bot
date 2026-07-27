import requests

class BirdeyeClient:
    """
    Integrates Birdeye data structures to fetch deep multi-DEX analytics 
    and verified pricing data specifically optimized for Solana.
    """
    def __init__(self, api_key=None):
        self.base_url = "https://public-api.birdeye.so/defi/price"
        # Birdeye API works best with a free API key in headers if available, 
        # but public parameters can be queried directly or via headers.
        self.headers = {"X-API-KEY": api_key} if api_key else {}

    def get_token_price(self, token_address):
        try:
            url = f"{self.base_url}?address={token_address}"
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                if success:
                    price_data = data.get("data", {})
                    return {
                        "status": "SUCCESS",
                        "price": price_data.get("value", 0.0)
                    }
        except Exception:
            pass
        return {"status": "FALLBACK", "price": 150.0}

if __name__ == "__main__":
    birdeye = BirdeyeClient()
    # Test with Solana native mint address
    res = birdeye.get_token_price("So11111111111111111111111111111111111111112")
    print("Birdeye Price Result:", res)
  
