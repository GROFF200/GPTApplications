# Monitors stocks, and provides alerts if a stock passes an entry or exit point.
# Stocks are sold if they pass an exit point as well.
# Uses the Alpaca Broker API for selling positions

import json
import time
from datetime import datetime, timedelta
from plyer import notification
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


# Alpaca API credentials
url = 'https://data.alpaca.markets/v1beta1/news'
api_key = '<key here>'
api_secret = '<key here>'
BASE_URL = 'https://api.alpaca.markets'

# Initialize Alpaca StockHistoricalDataClient
alpacaClient = StockHistoricalDataClient(api_key, api_secret)
trading_client = TradingClient(api_key, api_secret, url_override=BASE_URL)

# Function to fetch market data for a given stock symbol
def fetch_market_data(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    request_params = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start_date, end=end_date)
    stock_bars = alpacaClient.get_stock_bars(request_params).df
    latest_bar = stock_bars.iloc[-1]
    return latest_bar['close']

# Load config file
with open('config.json', 'r') as file:
    config = json.load(file)

# Function to place an order
def place_order(symbol, qty, side):
    # Preparing market order data
    market_order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide[side.upper()],
        time_in_force=TimeInForce.DAY
    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )


def check_market_data():
    for stock, values in config.items():
        print("Checking stock: "+stock);
        current_price = float(fetch_market_data(stock))
        print("Price: "+str(current_price))
        low_exit_point = float(values['low_exit_point'])
        if stock in owned_stocks:
            position = next((p for p in portfolio if p.symbol == stock), None)
            current_price = float(position.current_price) if position else current_price
            print("Position Current Price:"+str(current_price))
            position_qty = position.qty if position else 0
            

            if current_price <= values['low_exit_point']:
                place_sell_order(stock, position_qty, current_price, values['low_exit_point'])
            elif current_price >= values['high_exit_point']:
                place_sell_order(stock, position_qty, current_price, values['high_exit_point'])

        else:
            entry_point_range = (values['entry_point'] - 0.15, values['entry_point'] + 0.15)
            if entry_point_range[0] <= current_price <= entry_point_range[1]:
                print(f"Stock {stock} is within entry point range: Current Price: {current_price}")
                notification.notify(title=f"Stock Alert: Buy {stock}", message=f"{stock} is crossing entry point")

def place_sell_order(stock, qty, current_price, exit_point):
    print(f"Selling {qty} shares of {stock}. Current price {current_price} crossed exit point {exit_point}.\n")
    notification.notify(title=f"Stock Alert: Sell {stock}", message=f"Current price {current_price} crossed exit point {exit_point}")
    place_order(stock, qty, 'sell')

def is_market_open():
    now = datetime.now()
    return now.weekday() < 5 and (now.hour > 8 or (now.hour == 8 and now.minute >= 30)) and now.hour < 15


# Main monitoring loop
while True:
    # Check if market is open
    if is_market_open():
        print("Checking positions and watchlist symbols...");
        portfolio = trading_client.get_all_positions()
        owned_stocks = {position.symbol for position in portfolio}
        
        # Check prices for owned stocks every 5 minutes
        check_market_data()
        time.sleep(300)  # 5 minutes interval

        # Check prices for non-owned stocks every 15 minutes
        if time.time() % 900 == 0:
            check_market_data()
    else:
        print("Market is closed. Sleeping...")
        time.sleep(900)  # Sleep for 15 minutes before checking again