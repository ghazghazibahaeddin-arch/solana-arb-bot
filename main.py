import time
from datetime import datetime
from config import INITIAL_WALLET_BALANCE, MAX_RISK_PER_TRADE
from engine import scan_smart_market
from simulator import zero_error_simulation

# Live and smart system wallet tracking
current_wallet = INITIAL_WALLET_BALANCE
total_successful_trades = 0

def smart_logger(message):
    """Smart logger for recording actions and self-learning loops"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    try:
        with open("quantum_engine.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception:
        pass

def run_quantum_system():
    global current_wallet, total_successful_trades
    
    smart_logger("=" * 60)
    smart_logger(f"Initializing Quantum AI Arbitrage Engine | Wallet: ${current_wallet:.2f}")
    smart_logger("=" * 60)
    
    while True:
        try:
            # 1. Smart Market Scan
            market_data = scan_smart_market()
            
            if market_data:
                # 2. Run Zero-Error Simulation Shield
                simulation_result = zero_error_simulation(market_data)
                
                status = simulation_result.get("status")
                
                if status == "APPROVED":
                    profit = simulation_result.get("net_profit", 0)
                    total_successful_trades += 1
                    current_wallet += profit # Cumulative compound interest activation
                    
                    smart_logger(f"[EXECUTED] Route: {simulation_result['execution_path']} | Profit: +${profit:.4f} | New Wallet: ${current_wallet:.4f}")
                else:
                    reason = simulation_result.get("reason", "Unknown Risk")
                    smart_logger(f"[SECURELY BLOCKED] Reason: {reason}")
            else:
                smart_logger("Scanning decentralized liquidity pools...")
                
            # Smart delay to protect RPC node rate limits
            time.sleep(3)
            
        except KeyboardInterrupt:
            smart_logger("Engine safely stopped by user.")
            break
        except Exception as e:
            smart_logger(f"Critical System Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_quantum_system()
                
