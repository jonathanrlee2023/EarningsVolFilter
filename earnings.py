import asyncio
import datetime
import json
import os
import pprint
import re
import sqlite3
import time
from dotenv import load_dotenv
import finnhub
import pandas as pd

def next_friday_after_two_weeks():
    # 1. Start from today and jump ahead two weeks
    today = datetime.datetime.now().date()

    # 2. Compute days until the next Friday (weekday() → Monday=0 … Sunday=6; Friday=4)
    days_until_friday = (4 - today.weekday() + 7) % 7

    # 3. If target is already Friday, days_until_friday == 0 → stays the same
    next_friday = today + datetime.timedelta(days=days_until_friday)

    # 4. Format as ‘YYYY-MM-DD’
    return next_friday.strftime("%Y-%m-%d")

def write_upcoming_earnings_symbols(client):
    print("Entered")
    load_dotenv()  # Loads variables from .env into environment

    api_key = os.getenv("API_KEY")
    finnhub_client = finnhub.Client(api_key=api_key)


    # Get today's date
    today = datetime.datetime.today()   
    tmrw = today + datetime.timedelta(days=1) 
    next_friday = next_friday_after_two_weeks()

    # Format as YYYY-MM-DD
    _from = today.strftime('%Y-%m-%d')
    _to = tmrw.strftime('%Y-%m-%d')  # same day if you want just one day of earnings

    response = finnhub_client.earnings_calendar(
        _from=_from,
        to=_to,
        symbol="",  # Leave empty for all symbols
        international=False
    )

    # The response is already a dict
    # You can directly parse or print it
    calendar = response.get("earningsCalendar", [])
    tickers = []
    for entry in calendar:
        tickers.append(entry["symbol"])
    volatility_map = pd.Series(0.0, index=tickers)
    implied_move_map = pd.Series(0.0, index=tickers)
    for entry in calendar:
        try:
            symbol = entry["symbol"]

            response = client.option_chains(symbol=symbol, strikeCount=1, fromDate=today, toDate=next_friday).json()
            if response["numberOfContracts"] == 0: continue

            straddle_price = 0.0

            for exp_map_key in ("callExpDateMap", "putExpDateMap"):
                exp_map = response.get(exp_map_key, {})
                for expiry_bucket in exp_map.values():
                    for strike_level in expiry_bucket.values():
                        for contract in strike_level:
                            volatility_map[symbol] = contract["volatility"]
                            straddle_price += contract["mark"]

            response = client.quote(symbol_id=symbol).json()
            asset_price = response[symbol]['quote']['mark']

            implied_move_map[symbol] = straddle_price / asset_price * 100
            # Output
        except Exception as e:
            print(e)

    volatility_map = volatility_map[volatility_map != 0.0]
    sorted_map = volatility_map.sort_values(ascending=False)
    for key, value in sorted_map.items():
        print(f'{key}: {value}% IV; {implied_move_map[key]}% IM')  # (key, value)
