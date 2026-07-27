import os
from dotenv import load_dotenv


load_dotenv()



# APIs

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


HELIUS_API_KEY = os.getenv(
    "HELIUS_API_KEY"
)


BIRDEYE_API_KEY = os.getenv(
    "BIRDEYE_API_KEY"
)



# Scanner

SCAN_INTERVAL = 2



# Trading Rules

MIN_SCORE = 85


MAX_DAILY_TRADES = 1000



# Risk

MIN_LIQUIDITY = 10000


MAX_SLIPPAGE = 5



# Network

NETWORK = "mainnet-beta"
