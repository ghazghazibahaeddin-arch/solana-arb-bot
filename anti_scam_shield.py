class AntiScamShield:
    """
    Advanced security shield to detect spam tokens, honeypots, 
    and verify liquidity pool safety against rug pulls.
    """
    def __init__(self, min_liquidity_usd=5000.0):
        self.min_liquidity = min_liquidity_usd # Minimum safe liquidity in USD
        
    def verify_token_security(self, token_data):
        """
        Performs deep security checks on liquidity, honeypot risk, and spam indicators.
        """
        liquidity_usd = token_data.get("liquidity_usd", 0.0)
        is_honeypot = token_data.get("is_honeypot", False)
        is_lp_locked = token_data.get("is_lp_locked", True)
        is_spam = token_data.get("is_spam", False)
        
        # 1. Check for spam tokens
        if is_spam:
            return {
                "safe": False,
                "reason": "Token flagged as Spam/Airdrop scam."
            }
            
        # 2. Check for Honeypot (can you sell?)
        if is_honeypot:
            return {
                "safe": False,
                "reason": "CRITICAL: Honeypot detected! You cannot sell this token."
            }
            
        # 3. Check for locked liquidity to prevent zero-drop
        if not is_lp_locked:
            return {
                "safe": False,
                "reason": "Unsafe: Liquidity is not locked (Rug pull risk)."
            }
            
        # 4. Check minimum liquidity threshold
        if liquidity_usd < self.min_liquidity:
            return {
                "safe": False,
                "reason": f"Insufficient liquidity (${liquidity_usd} < ${self.min_liquidity}). Risk of slippage/zero drop."
            }
            
        return {
            "safe": True,
            "reason": "Token passed all anti-scam and liquidity safety checks."
        }

if __name__ == "__main__":
    shield = AntiScamShield(min_liquidity_usd=5000.0)
    
    # Test safe token case
    safe_token = {
        "liquidity_usd": 15000.0,
        "is_honeypot": False,
        "is_lp_locked": True,
        "is_spam": False
    }
    print("Safe Token Test:", shield.verify_token_security(safe_token))
    
    # Test scam/honeypot case
    scam_token = {
        "liquidity_usd": 20000.0,
        "is_honeypot": True,
        "is_lp_locked": True,
        "is_spam": False
    }
    print("Scam Token Test:", shield.verify_token_security(scam_token))
          
