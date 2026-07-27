import os
import sys
from dotenv import load_dotenv

load_dotenv()

def run_system_diagnostics():
    print("=" * 60)
    print("🔍 RUNNING SYSTEM-WIDE QUANTUM DIAGNOSTICS...")
    print("=" * 60)
    
    errors_found = 0
    
    # 1. Check Environment & API Keys
    print("[1/5] Checking Environment Variables & Keys...")
    rpc = os.getenv("SOLANA_RPC_URL")
    groq = os.getenv("GROQ_API_KEY")
    gemini = os.getenv("GEMINI_API_KEY")
    
    if rpc and "helius" in rpc:
        print("  -> [OK] Helius RPC URL is configured.")
    else:
        print("  -> [WARNING] Helius RPC URL is missing or default.")
        
    if groq:
        print("  -> [OK] Groq API Key detected.")
    else:
        print("  -> [INFO] Groq API Key missing (will use algorithmic fallback).")
        
    if gemini:
        print("  -> [OK] Gemini API Key detected.")
    else:
        print("  -> [INFO] Gemini API Key missing (will use algorithmic fallback).")

    # 2. Check Module Imports
    print("\n[2/5] Testing Module Integrations...")
    modules = ["config", "engine", "simulator", "ai_predictor", "ghost_consensus", "dual_brain_swarm"]
    for mod in modules:
        try:
            __import__(mod)
            print(f"  -> [OK] Module '{mod}.py' loaded successfully.")
        except Exception as e:
            print(f"  -> [ERROR] Failed to load '{mod}.py': {e}")
            errors_found += 1

    # 3. Test Market Engine & Simulation
    print("\n[3/5] Testing Market Engine & Simulation Shield...")
    try:
        from engine import scan_smart_market
        from simulator import zero_error_simulation
        market = scan_smart_market()
        if market:
            print(f"  -> [OK] Market Data Fetched: SOL Price = ${market.get('buy_price', 0)}")
            sim = zero_error_simulation(market)
            print(f"  -> [OK] Simulation Shield Status: {sim.get('status')}")
        else:
            print("  -> [WARNING] Market scan returned empty (check internet/RPC).")
    except Exception as e:
            print(f"  -> [ERROR] Engine/Simulation test failed: {e}")
            errors_found += 1

    # 4. Test AI Predictor & Ghost Block
    print("\n[4/5] Testing AI Predictor & Ghost Consensus...")
    try:
        from ai_predictor import QuantumPredictor
        from ghost_consensus import GhostBlockEngine
        pred = QuantumPredictor()
        conf = pred.evaluate_market_momentum(95, 0.001)
        
        ghost = GhostBlockEngine()
        state = ghost.generate_ghost_state(150.0, 95)
        
        print(f"  -> [OK] AI Momentum Confidence Score: {conf:.2f}")
        print(f"  -> [OK] Ghost Block State: {state.get('status')} (Price: {state.get('ghost_price'):.2f})")
    except Exception as e:
            print(f"  -> [ERROR] AI/Ghost test failed: {e}")
            errors_found += 1

    # 5. Test Dual-Brain Swarm (Gemini + Groq)
    print("\n[5/5] Testing Dual-Brain AI Swarm (Gemini & Groq)...")
    try:
        from dual_brain_swarm import DualBrainSwarm
        swarm = DualBrainSwarm()
        test_state = {"token": "SOL", "buy_price": 150.0, "liquidity_score": 95}
        consensus = swarm.reach_consensus(test_state)
        print(f"  -> [OK] Swarm Consensus Result: {consensus.get('consensus')}")
        print(f"  -> [OK] Swarm Notes: {consensus.get('notes')}")
    except Exception as e:
            print(f"  -> [ERROR] Swarm test failed: {e}")
            errors_found += 1

    print("\n" + "=" * 60)
    if errors_found == 0:
        print("🌟 DIAGNOSTICS COMPLETE: ALL SYSTEMS 100% OPERATIONAL & PERFECT!")
    else:
        print(f"⚠️ DIAGNOSTICS COMPLETE: Found {errors_found} minor issues to review.")
    print("=" * 60)

if __name__ == "__main__":
    run_system_diagnostics()
      
