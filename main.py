import time
import sys
from datetime import datetime
from config import INITIAL_WALLET_BALANCE
from engine import scan_smart_market
from simulator import zero_error_simulation
from ai_predictor import QuantumPredictor
from ghost_consensus import GhostBlockEngine
from dual_brain_swarm import DualBrainSwarm

# Initialize core system state & components
current_wallet = INITIAL_WALLET_BALANCE
total_successful_trades = 0
consecutive_errors = 0

predictor = QuantumPredictor()
ghost_engine = GhostBlockEngine()
ai_swarm = DualBrainSwarm()

def self_healing_logger(message, is_error=False):
    """Logs system events and handles automated error messaging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    try:
        mode = "a" if not is_error else "a"
        with open("quantum_execution.log", mode, encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception:
        pass

def run_fully_automated_system():
    global current_wallet, total_successful_trades, consecutive_errors
    
    self_healing_logger("=" * 70)
    self_healing_logger(f"SELF-HEALING QUANTUM SYSTEM INITIALIZED | Wallet: ${current_wallet:.2f}")
    self_healing_logger("=" * 70)
    
    while True:
        try:
            # Step 1: Sequential Market Scan
            market_data = scan_smart_market()
            
            if market_data:
                # Step 2: Zero-Error Simulation Shield
                sim_result = zero_error_simulation(market_data)
                
                if sim_result.get("status") == "APPROVED":
                    # Step 3: AI Predictive Momentum Check
                    confidence = predictor.evaluate_market_momentum(
                        market_data.get("liquidity_score", 0),
                        market_data.get("slippage", 0)
                    )
                    
                    # Step 4: Ghost Block Future Validation
                    ghost_state = ghost_engine.generate_ghost_state(
                        market_data.get("buy_price", 0.0), 
                        market_data.get("liquidity_score", 1.0)
                    )
                    is_ghost_safe = ghost_engine.verify_zero_loss_trajectory(
                        market_data.get("buy_price", 0.0), 
                        ghost_state
                    )
                    
                    if confidence >= 0.85 and is_ghost_safe:
                        # Step 5: Dual-Brain AI Swarm Consensus (Gemini + Groq)
                        consensus = ai_swarm.reach_consensus(market_data)
                        
                        if consensus["consensus"] == "UNANIMOUS_APPROVED":
                            profit = sim_result.get("net_profit", 0)
                            total_successful_trades += 1
                            current_wallet += profit # Compound interest growth
                            
                            self_healing_logger(f"[SUCCESS EXECUTED] Profit: +${profit:.4f} | Wallet: ${current_wallet:.4f}")
                            consecutive_errors = 0 # Reset error counter on success
                        else:
                            self_healing_logger(f"[AI VETOED] Trade bypassed safely: {consensus['notes']}")
                    else:
                        self_healing_logger(f"[GHOST SHIELD] Volatility blocked. Confidence: {confidence:.2f}")
                else:
                    self_healing_logger(f"[SIMULATION BLOCKED] Reason: {sim_result.get('reason', 'Risk Check')}")
            else:
                self_healing_logger("Scanning decentralized liquidity pools...")
                
            # Reset error state counter on successful loop iteration
            consecutive_errors = 0
            time.sleep(3)
            
        except KeyboardInterrupt:
            self_healing_logger("System safely terminated by user.")
            break
        except Exception as e:
            # Self-Healing Mechanism: Catch any unexpected network or code crash, log it, and recover automatically
            consecutive_errors += 1
            backoff_time = min(consecutive_errors * 5, 30) # Exponential backoff to protect API limits
            
            self_healing_logger(f"[SELF-HEALING RECOVERY] Error encountered: {e}. Auto-recovering in {backoff_time}s...", is_error=True)
            time.sleep(backoff_time)

if __name__ == "__main__":
    run_fully_automated_system()
    
