import os
import requests
from dotenv import load_dotenv

load_dotenv()
HELIUS_RPC = os.getenv("HELIUS_RPC_URL", "https://api.mainnet-beta.solana.com")

def get_dex_quotes():
    # في النسخة التجريبية الأولى، نقوم بجلب الأسعار الأساسية عبر DEX Screener API أو APIs الخاصة بالمنصات
    try:
        url = "https://api.dexscreener.com/latest/dex/pairs/solana/solusdc"
        response = requests.get(url).json()
        pairs = response.get("pairs", [])
        
        quotes = {}
        for pair in pairs:
            dex_id = pair.get("dexId")
            if dex_id in ["raydium", "orca"]:
                quotes[dex_id] = {
                    "price": float(pair.get("priceUsd", 0)),
                    "liquidity": pair.get("liquidity", {}).get("usd", 0)
                }
        return quotes
    except Exception as e:
        print(f"Error fetching quotes: {e}")
        return {}
              
