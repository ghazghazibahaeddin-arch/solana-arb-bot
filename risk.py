MIN_NET_PROFIT = 0.0001
MAX_SLIPPAGE = 0.005

def evaluate_risk(opportunity):
    if opportunity.get("status") != "CHECKED":
        return "REJECT"
    
    net_profit = opportunity.get("net_profit", 0)
    
    if net_profit < MIN_NET_PROFIT:
        return "REJECT_LOW_PROFIT"
        
    return "EXECUTE"
  
