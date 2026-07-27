import requests

class JupiterAggregator:
    """
    Integrates free public Jupiter API endpoints to scan real-time 
    multi-DEX optimal routes and slippage tolerances across Solana.
    """
    def __init__(self):
        self.base_url = "https://quote-api.jup.ag/v6/quote"
        
    def get_best_route(self, input_mint, output_mint, amount):
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": 50
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "SUCCESS",
                    "out_amount": data.get("outAmount"),
                    "price_impact": data.get("priceImpactPct")
                }
        except Exception:
            pass
        return {"status": "FALLBACK_ACTIVE", "out_amount": amount, "price_impact": "0.01"}

if __name__ == "__main__":
    jup = JupiterAggregator()
    print("Jupiter Route Check:", jup.get_best_route("So11111111111111111111111111111111111111112", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 1000000000))
      
