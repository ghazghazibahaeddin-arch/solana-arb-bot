import time
from scanner import scan_market
from arbitrage import calculate_arbitrage
from risk import evaluate_risk

def run_engine():
    print("Starting Solana Arbitrage Paper Trading Engine...")
    while True:
        try:
            market_data = scan_market()
            opportunity = calculate_arbitrage(market_data)
            
            if opportunity:
                print(f"Route: {opportunity['buy_dex']} -> {opportunity['sell_dex']}")
                print(f"Decision: {evaluate_risk(opportunity)} | Profit: {opportunity.get('net_profit', 0)}")
            
            time.sleep(5)
        except Exception as e:
            print(f"Error in execution loop: {e}")

if __name__ == "__main__":
    run_engine()
              
