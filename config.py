import os
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv(
    "RPC_URL",
    "https://api.mainnet-beta.solana.com"
)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY", "")
