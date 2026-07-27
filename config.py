import os
from dotenv import load_dotenv

load_dotenv()

# Helius RPC Endpoint Configuration
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://mainnet.helius-rpc.com/?api-key=5ee01e91-4efc-43b0-81f3-2b81d2ea7437")

# Capital & Risk Parameters for Micro-Wallet ($5.86)
INITIAL_WALLET_BALANCE = 5.86
MAX_RISK_PER_TRADE = 0.5   # Maximum risk per individual trade in USD ($0.50)
MIN_NET_PROFIT_USD = 0.002 # Minimum net profit required after gas fees
MAX_ALLOWED_SLIPPAGE = 0.003 # Maximum allowed slippage (0.3%)
