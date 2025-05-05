import argparse
from typing import List, Dict
from tabulate import tabulate
from services.api_service import APIService
from utils.helpers import send_email_alert

def display_crypto_data(data: List[Dict], currencies: List[str] = ["usd", "eur"]):
    """Display cryptocurrency data in a formatted table."""
    if not data:
        print("No data available")
        return
    
    headers = ["Rank", "Name", "Symbol"] + [curr.upper() for curr in currencies]
    
    table_data = []
    for coin in data:
        row = [
            coin.get("market_cap_rank", "N/A"),
            coin.get("name", "Unknown"),
            coin.get("symbol", "?").upper(),
        ]
        
        # Handle different price formats
        current_price = coin.get("current_price", {})
        for currency in currencies:
            if isinstance(current_price, dict):
                price = current_price.get(currency, "N/A")
            else:  # If current_price is direct value
                price = current_price if currency.lower() == "usd" else "N/A"
            
            # Format the price if it's a number
            if isinstance(price, (int, float)):
                row.append(f"{price:,.2f}")
            else:
                row.append(str(price))
        
        table_data.append(row)
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def get_top_cryptos(api: APIService, limit: int = 10, currencies: List[str] = ["usd"]) -> List[Dict]:
    """Fetch top cryptocurrencies by market cap."""
    if not currencies:
        currencies = ["usd"]
    
    all_data = []
    base_params = {
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }
    
    # Get data for first currency
    try:
        params = {**base_params, "vs_currency": currencies[0]}
        data = api.get("coins/markets", params=params)
        if not isinstance(data, list):
            return []
        
        # If only one currency needed, return as-is
        if len(currencies) == 1:
            return data
        
        # For additional currencies, get just the prices
        for currency in currencies[1:]:
            price_params = {
                "ids": ",".join([coin["id"] for coin in data]),
                "vs_currencies": currency
            }
            prices = api.get("simple/price", params=price_params)
            
            # Merge prices into existing data
            for coin in data:
                coin_id = coin["id"]
                if coin_id in prices:
                    if "current_price" not in coin:
                        coin["current_price"] = {}
                    coin["current_price"][currency] = prices[coin_id].get(currency)
        
        return data
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return []

def monitor_price(api: APIService, coin_id: str, threshold: float, currency: str = "usd"):
    """Monitor a specific cryptocurrency for price drops."""
    params = {
        "vs_currency": currency,
        "ids": coin_id
    }
    
    try:
        data = api.get("coins/markets", params=params)
        
        # Check if data is valid
        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"No valid data found for {coin_id}")
            return
        
        # Get the first coin (should be only one since we requested specific ID)
        coin = data[0]
        
        # Handle different price formats
        current_price = coin.get("current_price")
        if isinstance(current_price, dict):
            current_price = current_price.get(currency, 0)
        
        # Convert to float if it's a string
        if isinstance(current_price, str):
            try:
                current_price = float(current_price)
            except ValueError:
                current_price = 0
        
        print(f"Current price of {coin.get('name', coin_id)}: {current_price} {currency.upper()}")
        
        if current_price <= threshold:
            message = (f"Alert! {coin.get('name', coin_id)} price dropped to {current_price:.2f} {currency.upper()}\n"
                      f"24h Change: {coin.get('price_change_percentage_24h', 'N/A')}%\n"
                      f"Market Cap: {coin.get('market_cap', {}).get(currency, 'N/A'):,.2f}")
            
            print(message)
            send_email_alert(
                subject=f"Crypto Alert: {coin.get('name', coin_id)} Price Drop",
                body=message
            )
            
    except Exception as e:
        print(f"Error monitoring price: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Cryptocurrency Market Tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Top command
    top_parser = subparsers.add_parser("top", help="Get top cryptocurrencies")
    top_parser.add_argument("-n", "--number", type=int, default=10, help="Number of coins to display")
    top_parser.add_argument("-c", "--currencies", nargs="+", default=["usd"], help="Currencies to display")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor a cryptocurrency")
    monitor_parser.add_argument("coin", help="Coin ID (e.g., bitcoin)")
    monitor_parser.add_argument("-t", "--threshold", type=float, required=True, help="Price threshold for alert")
    monitor_parser.add_argument("-cu", "--currency", default="usd", help="Currency for threshold")
    
    args = parser.parse_args()
    api = APIService()
    
    if args.command == "top":
        data = get_top_cryptos(api, args.number, args.currencies)
        display_crypto_data(data, args.currencies)
    elif args.command == "monitor":
        monitor_price(api, args.coin, args.threshold, args.currency)

if __name__ == "__main__":
    main()