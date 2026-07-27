class BirdeyeHolderFilter:
    """
    Advanced token security and momentum sniper filter.
    Validates token age, top holder concentration, and allows 
    dynamic override for high-probability explosive arbitrage trades.
    """
    def __init__(self, max_top_holder_percentage=10.0):
        self.max_holder_pct = max_top_holder_percentage # Example: 10% max for a single holder
        
    def evaluate_token_opportunity(self, token_age_hours, top_holder_pct, momentum_score):
        """
        Evaluates safety rules, but overrides holder concentration 
        if the profit momentum score is exceptionally high (clear opportunity).
        """
        # Rule 1: Clear explosive opportunity override (Momentum > 90%)
        if momentum_score >= 0.90:
            return {
                "decision": "EXECUTE_AGGRESSIVE_SNIPE",
                "reason": "Explosive momentum detected; bypassing holder concentration limits to frontrun price surge."
            }
            
        # Rule 2: Standard strict safety checks
        if top_holder_pct > self.max_holder_pct:
            return {
                "decision": "REJECT",
                "reason": f"Holder concentration too high ({top_holder_pct}% > {self.max_holder_pct}%). Risk of whale dump."
            }
            
        if token_age_hours < 1:
            return {
                "decision": "REJECT",
                "reason": "Token too fresh (< 1 hour), high rug-pull probability."
            }
            
        return {
            "decision": "APPROVE_SAFE_TRADE",
            "reason": "Token passed age and holder distribution checks successfully."
        }

if __name__ == "__main__":
    # Test cases
    filter_engine = BirdeyeHolderFilter(max_top_holder_percentage=10.0)
    
    # Test clear high-momentum opportunity override
    print(filter_engine.evaluate_token_opportunity(token_age_hours=2, top_holder_pct=25.0, momentum_score=0.95))
    
    # Test standard safe trade
    print(filter_engine.evaluate_token_opportunity(token_age_hours=12, top_holder_pct=4.5, momentum_score=0.50))
              
