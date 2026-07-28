import os

from dotenv import load_dotenv

load_dotenv()


# =========================
# API KEYS
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY", "")


# =========================
# SOLANA NETWORK
# =========================

NETWORK = os.getenv("NETWORK", "mainnet-beta")

RPC_URL = os.getenv(
    "RPC_URL",
    "https://api.mainnet-beta.solana.com",
)


# =========================
# SCANNER
# =========================

SCAN_INTERVAL = 2


# =========================
# TRADING RULES
# =========================

MIN_SCORE = 85
MAX_DAILY_TRADES = 1000


# =========================
# RISK
# =========================

MIN_LIQUIDITY = 10000
MAX_SLIPPAGE = 5
