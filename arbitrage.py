def calculate_arbitrage(market_data):
    if not market_data:
        return None
        
    buy_dex = market_data.get("buy_dex", "Raydium")
    sell_dex = market_data.get("sell_dex", "Orca")
    buy_price = market_data.get("buy_price", 100.0)
    sell_price = market_data.get("sell_price", 101.5)
    
    gross_profit = sell_price - buy_price
    net_profit = gross_profit - (buy_price * 0.002)
    
    opportunity = {
        "status": "CHECKED",
        "buy_dex": buy_dex,
        "sell_dex": sell_dex,
        "net_profit": net_profit
    }
    return opportunity

