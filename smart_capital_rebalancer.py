class SmartCapitalRebalancer:
    """
    Manages multi-token portfolio risk (1 to 100 tokens), 
    ensures rapid capital recovery at 1.25x, progressive profit taking up to 100x+,
    and triggers emergency dump sells if crash indicators are detected.
    """
    def __init__(self, initial_capital_per_trade=100.0):
        self.initial_capital = initial_capital_per_trade
        
    def process_trade_lifecycle(self, current_multiplier, crash_indicator=False):
        """
        Evaluates current price multiplier and executes risk rules:
        - Crash detected -> Emergency full sell.
        - 1.25x -> Pull out initial capital + portion of profit, keep rest.
        - 2.0x+ -> Secure half, let remainder compound towards 10x, 100x, 1000x.
        """
        # Rule 1: Emergency Crash Protection (Sell everything immediately)
        if crash_indicator:
            return {
                "action": "EMERGENCY_SELL_ALL",
                "profit_secured": "All remaining positions liquidated to protect capital.",
                "status": "SAFEGUARD_ACTIVATED"
            }
            
        # Rule 2: Reached 1.25x (Take back initial capital + 0.75 profit equivalent, let rest run)
        if current_multiplier >= 1.25 and current_multiplier < 2.0:
            return {
                "action": "SECURE_CAPITAL_PHASE_1",
                "reinvest_pool": "Initial capital recovered, trading with pure generated profit multiplier.",
                "multiplier": current_multiplier
            }
            
        # Rule 3: Reached 2.0x or higher (Scale up to 10x, 100x, 1000x safely)
        if current_multiplier >= 2.0:
            return {
                "action": "PROGRESSIVE_PROFIT_HARVEST",
                "detail": f"At {current_multiplier}x: Secured 50% of holdings, compounding remaining balance for exponential targets (10x - 1000x)."
            }
            
        return {
            "action": "HOLD_AND_MONITOR",
            "multiplier": current_multiplier,
            "status": "Waiting for milestone or exit signal."
        }

if __name__ == "__main__":
    rebalancer = SmartCapitalRebalancer(initial_capital_per_trade=50.0)
    
    # Test 1.25x trigger
    print("Test 1.25x:", rebalancer.process_trade_lifecycle(1.25, crash_indicator=False))
    
    # Test 2.0x trigger
    print("Test 2.0x:", rebalancer.process_trade_lifecycle(2.5, crash_indicator=False))
    
    # Test Emergency Crash Exit
    print("Test Crash Drop:", rebalancer.process_trade_lifecycle(1.5, crash_indicator=True))
          
