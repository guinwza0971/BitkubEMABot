import os
import time # Correctly import the time module
import requests
import json
import hmac
import hashlib
from binance.client import Client
from datetime import datetime, timedelta, time as datetime_time # Alias datetime.time to avoid conflict
import pytz # Import pytz for timezone handling

# --- Configuration File Name ---
CONFIG_FILE = 'config.json'

# --- Bitkub API Configuration ---
BITKUB_API_HOST = 'https://api.bitkub.com'
BINANCE_API_HOST = 'https://api.binance.com' # Added for server time endpoint

# --- Helper Functions for API Calls ---
def get_binance_server_time_utc():
    """Fetches the current server time from Binance API and returns it as a UTC datetime object."""
    try:
        response = requests.get(f"{BINANCE_API_HOST}/api/v3/time", timeout=5)
        response.raise_for_status()
        server_time_ms = response.json()['serverTime']
        # Convert milliseconds to seconds and then to datetime object in UTC
        return datetime.fromtimestamp(server_time_ms / 1000, tz=pytz.utc)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Binance server time: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching Binance server time: {e}")
        return None

def generate_bitkub_signature(api_secret, timestamp, method, path, body_string=""):
    """Generates the HMAC SHA-256 signature for Bitkub API requests."""
    payload_parts = [str(timestamp), method, path]
    if method == 'POST':
        payload_parts.append(body_string)
    elif method == 'GET':
        # For GET, query parameters are part of the path for signing
        # Assuming path already includes query params if any
        pass
    
    payload_string = ''.join(payload_parts)
    return hmac.new(api_secret.encode('utf-8'), payload_string.encode('utf-8'), hashlib.sha256).hexdigest()

def bitkub_api_call(api_key, api_secret, method, path, params=None, json_body=None):
    """Makes a signed API call to Bitkub."""
    try:
        # Get server timestamp from Bitkub
        timestamp_response = requests.get(f"{BITKUB_API_HOST}/api/v3/servertime", timeout=5)
        timestamp_response.raise_for_status()
        timestamp = timestamp_response.json()

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-BTK-TIMESTAMP': str(timestamp),
            'X-BTK-APIKEY': api_key
        }

        request_url = f"{BITKUB_API_HOST}{path}"
        body_string = ""

        if method == 'GET':
            if params:
                query_string = requests.PreparedRequest().prepare_url(request_url, params).url.replace(request_url, "")
                request_url = f"{request_url}{query_string}"
                path_for_sign = f"{path}{query_string}" # Path for signing includes query string
            else:
                path_for_sign = path
            signature = generate_bitkub_signature(api_secret, timestamp, method, path_for_sign)
            headers['X-BTK-SIGN'] = signature
            response = requests.request(method, request_url, headers=headers, timeout=10)
        elif method == 'POST':
            if json_body:
                body_string = json.dumps(json_body)
            signature = generate_bitkub_signature(api_secret, timestamp, method, path, body_string)
            headers['X-BTK-SIGN'] = signature
            response = requests.request(method, request_url, headers=headers, data=body_string, timeout=10)
        else:
            raise ValueError("Unsupported HTTP method for Bitkub API.")

        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Bitkub API Request Error ({method} {path}): {e}")
        return {"error": -1, "message": str(e)} # Custom error format
    except json.JSONDecodeError:
        print(f"Bitkub API JSON Decode Error: Could not parse response from {request_url}")
        return {"error": -2, "message": "Invalid JSON response"}
    except Exception as e:
        print(f"An unexpected error occurred during Bitkub API call: {e}")
        return {"error": -3, "message": str(e)}


# --- Helper Functions for MA Calculation ---
def calculate_sma(prices, period):
    """Calculates the Simple Moving Average (SMA)."""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_ema(prices, period):
    """Calculates the Exponential Moving Average (EMA)."""
    if len(prices) < period:
        return None
    
    # Calculate the smoothing multiplier
    multiplier = 2 / (period + 1)
    
    # Initialize EMA with SMA for the first 'period' prices
    ema = sum(prices[:period]) / period
    
    # Calculate EMA for subsequent prices
    for price in prices[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema

def calculate_wma(prices, period):
    """Calculates the Weighted Moving Average (WMA)."""
    if len(prices) < period:
        return None
    
    weights = list(range(1, period + 1))
    sum_weights = sum(weights)
    
    wma = sum(price * weight for price, weight in zip(prices[-period:], weights)) / sum_weights
    return wma

def calculate_ma(prices, period, ma_type):
    """
    Calculates the specified Moving Average (MA).

    Args:
        prices (list): A list of numerical prices.
        period (int): The number of periods for the MA calculation.
        ma_type (str): Type of moving average ('SMA', 'EMA', 'WMA').

    Returns:
        float: The calculated MA, or None if there aren't enough prices.
    """
    if ma_type.upper() == 'SMA':
        return calculate_sma(prices, period)
    elif ma_type.upper() == 'EMA':
        return calculate_ema(prices, period)
    elif ma_type.upper() == 'WMA':
        return calculate_wma(prices, period)
    else:
        print(f"Error: Unsupported MA type '{ma_type}'. Using SMA as fallback.")
        return calculate_sma(prices, period)


def get_display_decimals(price):
    """
    Determines the number of decimal places to display based on the price magnitude.
    """
    if price is None:
        return 2 # Default for None
    if price >= 1000:
        return 2
    elif price >= 100:
        return 3
    elif price >= 10:
        return 4
    elif price >= 1:
        return 5
    elif price >= 0.1:
        return 6
    elif price >= 0.01:
        return 7
    else: # For very small prices
        return 8

def get_crypto_data_and_mas(symbol, interval, ma_periods, fetch_limit, client, ma_type):
    """
    Fetches historical close prices for a given cryptocurrency symbol from Binance
    at a specified interval and calculates specified Moving Averages
    for the period before the latest fetched period and the period before that.

    Args:
        symbol (str): The trading pair symbol (e.g., 'HYPERUSDT').
        interval (str): The candlestick interval (e.g., '1s', '1m', '1h', '1d', '1w').
        ma_periods (list): A list of integer periods for MA calculation (e.g., [10, 20]).
                            Assumes ma_periods[0] is fast MA, ma_periods[1] is slow MA.
        fetch_limit (int): The total number of past periods to fetch.
                           Should be at least the largest MA period + 2 to calculate
                           MAs for the current and previous confirmed candles.
        client (binance.client.Client): The initialized Binance client (can be None for free API).
        ma_type (str): Type of moving average ('SMA', 'EMA', 'WMA').

    Returns:
        dict: A dictionary containing:
              - 'close_prices': List of fetched close prices.
              - 'current_confirmed_mas': Dictionary of calculated MAs for the latest confirmed candle.
              - 'previous_confirmed_mas': Dictionary of calculated MAs for the candle before the latest confirmed.
    """
    # Map string interval to Binance Client constant
    binance_interval_map = {
        '1s': Client.KLINE_INTERVAL_1SECOND,
        '1m': Client.KLINE_INTERVAL_1MINUTE,
        '3m': Client.KLINE_INTERVAL_3MINUTE,
        '5m': Client.KLINE_INTERVAL_5MINUTE,
        '15m': Client.KLINE_INTERVAL_15MINUTE,
        '30m': Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR,
        '2h': Client.KLINE_INTERVAL_2HOUR,
        '4h': Client.KLINE_INTERVAL_4HOUR,
        '6h': Client.KLINE_INTERVAL_6HOUR,
        '8h': Client.KLINE_INTERVAL_8HOUR,
        '12h': Client.KLINE_INTERVAL_12HOUR,
        '1d': Client.KLINE_INTERVAL_1DAY,
        '3d': Client.KLINE_INTERVAL_3DAY,
        '1w': Client.KLINE_INTERVAL_1WEEK,
        '1M': Client.KLINE_INTERVAL_1MONTH,
    }

    binance_interval = binance_interval_map.get(interval)
    if not binance_interval:
        print(f"Error: Invalid interval '{interval}'. Supported intervals: {list(binance_interval_map.keys())}")
        return {'close_prices': [], 'current_confirmed_mas': {}, 'previous_confirmed_mas': {}}

    try:
        # Fetch historical klines (candlestick data)
        # Assuming free API access to get_klines without API key/secret
        klines = client.get_klines(symbol=symbol, interval=binance_interval, limit=fetch_limit)

        if not klines:
            print(f"No klines data fetched for {symbol} with interval {interval}.")
            return {'close_prices': [], 'current_confirmed_mas': {}, 'previous_confirmed_mas': {}}

        close_prices = []
        for kline in klines:
            close_price = float(kline[4])
            close_prices.append(close_price)

        # Ensure we have enough data for both current and previous MAs
        max_ma_period = max(ma_periods)
        if len(close_prices) < max_ma_period + 2:
            print(f"Not enough data ({len(close_prices)} candles) to calculate both current and previous confirmed MAs for periods {ma_periods}. Need at least {max_ma_period + 2} candles.")
            return {'close_prices': close_prices, 'current_confirmed_mas': {}, 'previous_confirmed_mas': {}}

        # Calculate MAs for the latest confirmed candle (excluding the current unconfirmed one)
        prices_for_current_confirmed_ma = close_prices[:-1]

        current_confirmed_mas = {}
        for period in ma_periods:
            ma_value = calculate_ma(prices_for_current_confirmed_ma, period, ma_type)
            if ma_value is not None:
                current_confirmed_mas[period] = ma_value

        # Calculate MAs for the candle before the latest confirmed one
        prices_for_previous_confirmed_ma = close_prices[:-2]

        previous_confirmed_mas = {}
        for period in ma_periods:
            ma_value = calculate_ma(prices_for_previous_confirmed_ma, period, ma_type)
            if ma_value is not None:
                previous_confirmed_mas[period] = ma_value

        return {
            'close_prices': close_prices,
            'current_confirmed_mas': current_confirmed_mas,
            'previous_confirmed_mas': previous_confirmed_mas
        }

    except Exception as e:
        print(f"An error occurred during data fetch: {e}")
        return {'close_prices': [], 'current_confirmed_mas': {}, 'previous_confirmed_mas': {}}

def get_bitkub_market_data(symbol):
    """
    Fetches current ticker information for a given symbol from Bitkub,
    including last, lowestAsk, and highestBid prices.
    """
    try:
        url = f"https://api.bitkub.com/api/market/ticker?sym={symbol}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if symbol in data:
            return {
                'last': float(data[symbol].get('last')),
                'lowestAsk': float(data[symbol].get('lowestAsk')),
                'highestBid': float(data[symbol].get('highestBid'))
            }
        else:
            print(f"Error: Symbol '{symbol}' not found in Bitkub ticker response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market data for {symbol} from Bitkub API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching Bitkub market data for {symbol}: {e}")
        return None

def place_buy_order_bitkub(api_key, api_secret, bitkub_symbol_config, amount_thb, order_type, rate=None, signal_type="primary"):
    """
    Places a buy order on Bitkub.
    Args:
        api_key (str): Bitkub API Key.
        api_secret (str): Bitkub API Secret.
        bitkub_symbol_config (str): The trading pair from config (e.g., 'THB_OMNI').
        amount_thb (float): The amount of THB to spend.
        order_type (str): 'limit' or 'market'.
        rate (float, optional): The price at which to place the limit order. Required if order_type is 'limit'.
        signal_type (str): 'primary' or 'backup' to indicate the signal source.
    Returns:
        dict: The response from the Bitkub API.
    """
    # Convert THB_OMNI to omni_thb for API call
    base_currency = bitkub_symbol_config.split('_')[1]
    quote_currency = bitkub_symbol_config.split('_')[0]
    api_symbol = f"{base_currency.lower()}_{quote_currency.lower()}"

    print(f"REAL BUY ({signal_type.upper()} SIGNAL): Attempting to buy {bitkub_symbol_config} with {amount_thb} THB using {order_type} order...")
    path = '/api/v3/market/place-bid'
    json_body = {
        'sym': api_symbol,
        'amt': float(f'{amount_thb:.{get_display_decimals(amount_thb)}f}'), # Amount of THB to spend
        'typ': order_type
    }
    if order_type == 'limit' and rate is not None:
        json_body['rat'] = float(f'{rate:.{get_display_decimals(rate)}f}')
        print(f"  Limit rate set to: {rate:.{get_display_decimals(rate)}f}")
    elif order_type == 'market':
        # For market buy, 'rat' is not typically used or can be omitted.
        # Bitkub's sample implies 'rat' can be present, but it's usually ignored for market orders.
        # We will not set 'rat' for market orders here.
        pass

    response = bitkub_api_call(api_key, api_secret, 'POST', path, json_body=json_body)
    if response and response.get('error') == 0:
        print(f"REAL BUY SUCCESS: Order ID {response['result'].get('id')}, received approx. {response['result'].get('rec', 'N/A')} {base_currency}.")
    else:
        print(f"REAL BUY FAILED: {response.get('message', 'Unknown error')}. Error code: {response.get('error', 'N/A')}")
    return response

def place_sell_order_bitkub(api_key, api_secret, bitkub_symbol_config, coin_amount, order_type, rate=None, signal_type="primary"):
    """
    Places a sell order on Bitkub.
    Args:
        api_key (str): Bitkub API Key.
        api_secret (str): Bitkub API Secret.
        bitkub_symbol_config (str): The trading pair from config (e.g., 'THB_OMNI').
        coin_amount (float): The amount of coin to sell.
        order_type (str): 'limit' or 'market'.
        rate (float, optional): The price at which to place the limit order. Required if order_type is 'limit'.
        signal_type (str): 'primary' or 'backup' to indicate the signal source.
    Returns:
        dict: The response from the Bitkub API.
    """
    # Convert THB_OMNI to omni_thb for API call
    base_currency = bitkub_symbol_config.split('_')[1]
    quote_currency = bitkub_symbol_config.split('_')[0]
    api_symbol = f"{base_currency.lower()}_{quote_currency.lower()}"

    print(f"REAL SELL ({signal_type.upper()} SIGNAL): Attempting to sell {coin_amount:.8f} {base_currency} using {order_type} order...")
    path = '/api/v3/market/place-ask'
    json_body = {
        'sym': api_symbol,
        'amt': float(f'{coin_amount:.8f}'), # Amount of coin to sell
        'typ': order_type
    }
    if order_type == 'limit' and rate is not None:
        json_body['rat'] = float(f'{rate:.{get_display_decimals(rate)}f}')
        print(f"  Limit rate set to: {rate:.{get_display_decimals(rate)}f}")
    elif order_type == 'market':
        # For market sell, 'rat' is not typically used or can be omitted.
        # We will not set 'rat' for market orders here.
        pass

    response = bitkub_api_call(api_key, api_secret, 'POST', path, json_body=json_body)
    if response and response.get('error') == 0:
        print(f"REAL SELL SUCCESS: Order ID {response['result'].get('id')}, received approx. {response['result'].get('rec', 'N/A')} {quote_currency}.")
    else:
        print(f"REAL SELL FAILED: {response.get('message', 'Unknown error')}. Error code: {response.get('error', 'N/A')}")
    return response

def get_bitkub_balance(api_key, api_secret, currency):
    """Fetches the available balance for a specific currency from Bitkub."""
    path = '/api/v3/market/balances'
    response = bitkub_api_call(api_key, api_secret, 'POST', path) # Balances endpoint is POST with no body/params
    
    if response and response.get('error') == 0:
        balances = response['result']
        if currency in balances:
            return float(balances[currency]['available'])
        else:
            print(f"Currency '{currency}' not found in Bitkub balances.")
            return 0.0
    else:
        print(f"Failed to fetch Bitkub balances: {response.get('message', 'Unknown error')}. Error code: {response.get('error', 'N/A')}")
        return 0.0

def load_config():
    """Loads configuration from config.json or prompts user to create it."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        print(f"Configuration loaded from {CONFIG_FILE}")
        return config
    else:
        print(f"'{CONFIG_FILE}' not found. Let's create it.")
        return get_user_input_and_create_config()

def get_user_input_and_create_config():
    """Prompts user for configuration settings and saves them to config.json."""
    config = {}

    print("\nPlease provide the following configuration details:")

    config['bitkub_api_key'] = input("Enter your Bitkub API Key: ").strip()
    config['bitkub_api_secret'] = input("Enter your Bitkub API Secret: ").strip()

    # Binance API keys are no longer prompted, but kept in config structure as empty strings
    config['binance_api_key'] = ""
    config['binance_api_secret'] = ""

    config['bitkub_symbol'] = input("Enter Coin to trade in Bitkub format (e.g., THB_BTC): ").strip().upper()
    # For Binance, the symbol is usually BASEASSET+QUOTEASSET (e.g., BTCUSDT)
    # User needs to specify the correct Binance pair for the base asset against USDT or a major stablecoin
    config['binance_symbol'] = input(f"Enter corresponding Binance symbol for historical data (e.g., {config['bitkub_symbol'].split('_')[1]}USDT): ").strip().upper()


    while True:
        try:
            config['position_size_thb'] = float(input("Enter default position size in THB (e.g., 1000): "))
            if config['position_size_thb'] <= 0:
                raise ValueError("Position size must be positive.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter a positive number.")

    while True:
        try:
            config['trading_fee_percentage'] = float(input("Enter trading fee percentage (e.g., 0.25 for 0.25%): ")) / 100
            if not (0 <= config['trading_fee_percentage'] <= 1):
                raise ValueError("Fee percentage must be between 0 and 100.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter a number between 0 and 100.")

    print("\n--- Indicator Settings ---")
    indicator_settings = {}
    while True:
        try:
            indicator_settings['fast_ma_period'] = int(input("Enter Fast MA period (default 10): ") or "10")
            if indicator_settings['fast_ma_period'] <= 0:
                raise ValueError("Period must be positive.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter a positive integer.")

    while True:
        try:
            indicator_settings['slow_ma_period'] = int(input("Enter Slow MA period (default 20): ") or "20")
            if indicator_settings['slow_ma_period'] <= 0:
                raise ValueError("Period must be positive.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter a positive integer.")

    while True:
        indicator_type = input("Enter type of indicator (SMA, EMA, WMA, default EMA): ").strip().upper() or "EMA"
        if indicator_type in ['SMA', 'EMA', 'WMA']:
            indicator_settings['indicator_type'] = indicator_type
            break
        else:
            print("Invalid indicator type. Please choose from SMA, EMA, or WMA.")
    config['indicator_settings'] = indicator_settings

    while True:
        # Reverted to Binance supported intervals
        timeframe = input("Enter timeframe (e.g., 1s, 1m, 1h, 1d, 1w, default 1w for production, 1s for testing): ").strip() or "1w"
        # Basic validation for common intervals, can be expanded
        if timeframe in ['1s', '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']:
            config['timeframe'] = timeframe
            break
        else:
            print("Invalid timeframe. Please enter a valid interval (e.g., 1s, 1m, 1d, 1w).")

    while True:
        order_type_input = input("Choose order execution type (limit/market, default limit): ").strip().lower() or "limit"
        if order_type_input in ['limit', 'market']:
            config['order_execution_type'] = order_type_input
            break
        else:
            print("Invalid order type. Please enter 'limit' or 'market'.")

    config['max_tolerable_slippage_percentage'] = 0.0
    if config['order_execution_type'] == 'limit':
        while True:
            try:
                slippage_input = input("Enter maximum tolerable slippage in percentage (e.g., 2.0 for 2%, default 2.0): ") or "2.0"
                config['max_tolerable_slippage_percentage'] = float(slippage_input)
                if not (0 <= config['max_tolerable_slippage_percentage'] <= 100):
                    raise ValueError("Slippage percentage must be between 0 and 100.")
                break
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter a number between 0 and 100.")

    while True:
        self_buy_enabled_str = input("Enable initial buy at startup (for testing/starting with a position)? (true/false, default false): ").strip().lower() or "false"
        if self_buy_enabled_str in ['true', 'false']:
            config['self_buy_enabled'] = self_buy_enabled_str == 'true'
            break
        else:
            print("Invalid input. Please enter 'true' or 'false'.")

    config['self_buy_amount_coin'] = 0.0
    if config['self_buy_enabled']:
        while True:
            try:
                config['self_buy_amount_coin'] = float(input("Enter initial buy amount in coin unit (e.g., 0.001 BTC or 100 HYPER): "))
                if config['self_buy_amount_coin'] < 0:
                    raise ValueError("Initial buy amount cannot be negative.")
                break
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter a non-negative number.")

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Configuration saved to {CONFIG_FILE}.")
    return config

def format_seconds_to_hms(seconds):
    """Converts a duration in seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{remaining_seconds:02}"


def monitor_mas_on_candle_close():
    """
    Monitors cryptocurrency price data and calculates MAs, updating after each candle close.
    Detects MA crossovers, prints signals, reports derived bot state, and performs real trades on Bitkub.
    Settings are loaded from config.json.
    """
    config = load_config()

    bitkub_api_key = config['bitkub_api_key']
    bitkub_api_secret = config['bitkub_api_secret']
    binance_api_key = config['binance_api_key'] # Will be empty string
    binance_api_secret = config['binance_api_secret'] # Will be empty string

    binance_symbol = config['binance_symbol']
    bitkub_symbol = config['bitkub_symbol'] # e.g., THB_OMNI
    position_size_thb = config['position_size_thb']
    trading_fee_percentage = config['trading_fee_percentage']
    fast_ma_period = config['indicator_settings']['fast_ma_period']
    slow_ma_period = config['indicator_settings']['slow_ma_period']
    ma_type = config['indicator_settings']['indicator_type']
    interval = config['timeframe']
    self_buy_enabled = config['self_buy_enabled']
    self_buy_amount_coin = config['self_buy_amount_coin']
    order_execution_type = config['order_execution_type']
    max_slippage_percentage = config['max_tolerable_slippage_percentage']

    # Determine fetch_limit based on the largest MA period
    fetch_limit = max(fast_ma_period, slow_ma_period) + 2

    if fast_ma_period >= slow_ma_period:
        print("Warning: Fast MA period should be less than Slow MA period for typical crossover strategy.")

    # Map string interval to its duration in seconds
    interval_duration_seconds = {
        '1s': 1, '1m': 60, '3m': 3 * 60, '5m': 5 * 60, '15m': 15 * 60, '30m': 30 * 60,
        '1h': 60 * 60, '2h': 2 * 60 * 60, '4h': 4 * 60 * 60, '6h': 6 * 60 * 60,
        '8h': 8 * 60 * 60, '12h': 12 * 60 * 60, '1d': 24 * 60 * 60, '3d': 3 * 24 * 60 * 60,
        '1w': 7 * 24 * 60 * 60, '1M': 30 * 24 * 60 * 60 # Approximation for month
    }

    if interval not in interval_duration_seconds:
        print(f"Error: Unsupported interval '{interval}'. Supported intervals: {list(interval_duration_seconds.keys())}")
        return

    duration_sec = interval_duration_seconds[interval]
    print(f"Starting {ma_type} crossover monitoring for {binance_symbol} at {interval} interval. Press Ctrl+C to stop.")

    # Initialize Binance client with potentially empty API keys
    binance_client = Client(binance_api_key, binance_api_secret)

    # Trading state variables
    base_currency = bitkub_symbol.split('_')[1] # e.g., OMNI from THB_OMNI
    quote_currency = bitkub_symbol.split('_')[0] # e.g., THB from THB_OMNI

    bot_managed_holding = 0.0 # Amount of coin managed by the bot strategy
    last_trade_type = None # 'BUY', 'SELL', or None

    # Get initial THB and Coin balances from Bitkub (for display purposes only)
    initial_thb_balance = get_bitkub_balance(bitkub_api_key, bitkub_api_secret, quote_currency)
    initial_coin_balance = get_bitkub_balance(bitkub_api_key, bitkub_api_secret, base_currency)

    print(f"Initial Bitkub {quote_currency} balance: {initial_thb_balance:.2f}")
    print(f"Initial Bitkub {base_currency} balance: {initial_coin_balance:.8f} (Total account balance)")

    # Set initial bot_managed_holding based on self-buy config
    if self_buy_enabled and self_buy_amount_coin > 0:
        bot_managed_holding = self_buy_amount_coin
        last_trade_type = 'BUY'
        print(f"Initial buy enabled: Bot starts with {bot_managed_holding:.8f} {base_currency} (simulated managed holding).")
    else:
        # If self-buy is not enabled or amount is 0, bot starts with no managed holding
        bot_managed_holding = 0.0
        last_trade_type = 'SELL' # Assume bot is in 'cash' state if not managing any coin
        print(f"Initial bot managed holding: {bot_managed_holding:.8f} {base_currency} (cash).")
    
    previous_derived_bot_state = "UNKNOWN" # Will be updated after first MA calculation

    print(f"Initial last trade type: {last_trade_type}")
    print(f"Initial previous derived bot state: {previous_derived_bot_state}")


    while True:
        try:
            binance_server_time_utc = get_binance_server_time_utc()
            if binance_server_time_utc is None:
                print("Could not get Binance server time. Retrying in 5 seconds...")
                time.sleep(5)
                continue

            # Print Binance server time in HH:MM:SS format
            print(f"Binance Server Time (UTC): {binance_server_time_utc.strftime('%H:%M:%S')}")

            # Optimized update interval logic for specific timeframes
            wait_time_seconds = 0 # Default to no extra wait, let candle close logic handle it

            if interval in ['1d', '1w', '1M', '3d', '2h', '4h', '6h', '8h', '12h']: # Group these for 10-minute updates
                wait_time_seconds = 600 # 10 minutes
                print(f"Waiting {format_seconds_to_hms(wait_time_seconds)} for next update ({interval} timeframe specific)...")
                time.sleep(wait_time_seconds)

            elif interval == '1m':
                wait_time_seconds = 10
                print(f"Waiting {format_seconds_to_hms(wait_time_seconds)} for next update ({interval} timeframe specific)...")
                time.sleep(wait_time_seconds)
            elif interval == '3m':
                wait_time_seconds = 20
                print(f"Waiting {format_seconds_to_hms(wait_time_seconds)} for next update ({interval} timeframe specific)...")
                time.sleep(wait_time_seconds)
            elif interval == '5m':
                wait_time_seconds = 30
                print(f"Waiting {format_seconds_to_hms(wait_time_seconds)} for next update ({interval} timeframe specific)...")
                time.sleep(wait_time_seconds)
            elif interval == '15m':
                wait_time_seconds = 60
                print(f"Waiting {format_seconds_to_hms(wait_time_seconds)} for next update ({interval} timeframe specific)...")
                time.sleep(wait_time_seconds)
            elif interval == '30m':
                wait_time_seconds = 60
                print(f"Waiting {format_seconds_to_hms(wait_time_seconds)} for next update ({interval} timeframe specific)...")
                time.sleep(wait_time_seconds)
            elif interval == '1h':
                wait_time_seconds = 300 # 5 minutes
                print(f"Waiting {format_seconds_to_hms(wait_time_seconds)} for next update ({interval} timeframe specific)...")
                time.sleep(wait_time_seconds)
            else:
                # Original logic for other timeframes (wait until candle closes)
                # This block will only be hit if interval is not '1d', '1w', '1M', '3d' and not one of the custom intervals
                # Calculate based on Binance server time
                current_unix_ms_binance = int(binance_server_time_utc.timestamp() * 1000)
                interval_duration_ms = duration_sec * 1000
                current_interval_start_ms = (current_unix_ms_binance // interval_duration_ms) * interval_duration_ms
                expected_current_candle_close_ms = current_interval_start_ms + interval_duration_ms - 1
                next_candle_close_time_ms = expected_current_candle_close_ms + interval_duration_ms
                time_to_wait_ms = next_candle_close_time_ms - current_unix_ms_binance

                if time_to_wait_ms > 0:
                    print(f"Waiting {format_seconds_to_hms(time_to_wait_ms / 1000)} for the next {interval} candle to close...")
                    time.sleep(time_to_wait_ms / 1000)
                else:
                    print(f"Already past expected {interval} candle close time, fetching immediately.")

            # Now that the candle should have closed (or custom interval passed), fetch the data and calculate MAs
            data = get_crypto_data_and_mas(binance_symbol, interval, [fast_ma_period, slow_ma_period], fetch_limit, binance_client, ma_type)

            current_confirmed_mas = data['current_confirmed_mas']
            previous_confirmed_mas = data['previous_confirmed_mas']

            if current_confirmed_mas and previous_confirmed_mas:
                # Print current status
                print(f"\n--- Update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({interval} interval) ---")
                
                # Check if close_prices has at least 2 elements for latest confirmed price
                if len(data['close_prices']) >= 2:
                    latest_confirmed_price = data['close_prices'][-2]
                    decimals = get_display_decimals(latest_confirmed_price)
                    print(f"Latest confirmed close price ({binance_symbol}): {latest_confirmed_price:.{decimals}f}")
                else:
                    print(f"Not enough close price data for latest confirmed price for {binance_symbol}.")

                for period in [fast_ma_period, slow_ma_period]:
                    current_ma = current_confirmed_mas.get(period)
                    previous_ma = previous_confirmed_mas.get(period)
                    
                    current_ma_decimals = get_display_decimals(current_ma)
                    previous_ma_decimals = get_display_decimals(previous_ma)

                    if current_ma is not None and previous_ma is not None:
                        print(f"  {period}-{interval} {ma_type} (Current Confirmed): {current_ma:.{current_ma_decimals}f}")
                        print(f"  {period}-{interval} {ma_type} (Previous Confirmed): {previous_ma:.{previous_ma_decimals}f}")
                    else:
                        print(f"  Not enough data for {period}-{interval} {ma_type} calculation.")

                # Crossover Detection Logic
                fast_ma_current = current_confirmed_mas.get(fast_ma_period)
                slow_ma_current = current_confirmed_mas.get(slow_ma_period)
                fast_ma_previous = previous_confirmed_mas.get(fast_ma_period)
                slow_ma_previous = previous_confirmed_mas.get(slow_ma_period)

                if all(ma is not None for ma in [fast_ma_current, slow_ma_current, fast_ma_previous, slow_ma_previous]):
                    # Determine current derived bot state
                    if fast_ma_current > slow_ma_current:
                        derived_bot_state = "HOLDING"
                    else:
                        derived_bot_state = "CASH"
                    print(f"Current derived bot state: {derived_bot_state}")

                    # Fetch current Bitkub market data for actual trading
                    bitkub_market_data = get_bitkub_market_data(bitkub_symbol) 

                    if bitkub_market_data is None or bitkub_market_data.get('lowestAsk') is None or bitkub_market_data.get('highestBid') is None:
                        print("Could not fetch current Bitkub ask/bid prices. Skipping trade actions this cycle.")
                        continue # Skip trading actions if prices aren't available

                    current_bitkub_ask_price = bitkub_market_data['lowestAsk']
                    current_bitkub_bid_price = bitkub_market_data['highestBid']

                    # Check for Primary Buy Signal
                    if fast_ma_current > slow_ma_current and fast_ma_previous <= slow_ma_previous:
                        print(f"!!! PRIMARY BUY SIGNAL DETECTED !!! {fast_ma_period}-{interval} {ma_type} crossed ABOVE {slow_ma_period}-{interval} {ma_type}.")
                        # Check if bot is not already in a 'BUY' state with managed holdings
                        if last_trade_type != 'BUY' or bot_managed_holding == 0.0:
                            order_rate = None
                            if order_execution_type == 'limit':
                                order_rate = current_bitkub_ask_price * (1 + max_slippage_percentage / 100)
                                print(f"  Calculated buy limit rate with slippage: {order_rate:.{get_display_decimals(order_rate)}f}")
                            
                            # Attempt to place a real buy order on Bitkub
                            buy_response = place_buy_order_bitkub(
                                bitkub_api_key, bitkub_api_secret, bitkub_symbol, position_size_thb, order_execution_type, order_rate, signal_type="primary"
                            )
                            if buy_response and buy_response.get('error') == 0:
                                # Assuming 'rec' in result is the received coin amount
                                received_coin = float(buy_response['result'].get('rec', 0.0))
                                bot_managed_holding += received_coin # Add purchased amount to managed holding
                                last_trade_type = 'BUY'
                                print(f"Real primary buy SUCCESS. Bot now manages: {bot_managed_holding:.8f} {base_currency}.")
                            else:
                                print("Real primary buy order failed, not updating bot managed holding.")
                        else:
                            print("Already in a 'HOLDING' state (from previous buy) with managed coins, skipping primary buy order.")

                    # Check for Primary Sell Signal
                    elif fast_ma_current < slow_ma_current and fast_ma_previous >= slow_ma_previous:
                        print(f"!!! PRIMARY SELL SIGNAL DETECTED !!! {fast_ma_period}-{interval} {ma_type} crossed BELOW {slow_ma_period}-{interval} {ma_type}.")
                        # Check if bot is currently holding coins it manages (or if last trade was a buy)
                        if bot_managed_holding > 0 and last_trade_type != 'SELL':
                            order_rate = None
                            if order_execution_type == 'limit':
                                order_rate = current_bitkub_bid_price * (1 - max_slippage_percentage / 100)
                                print(f"  Calculated sell limit rate with slippage: {order_rate:.{get_display_decimals(order_rate)}f}")

                            # Attempt to place a real sell order on Bitkub
                            sell_response = place_sell_order_bitkub(
                                bitkub_api_key, bitkub_api_secret, bitkub_symbol, bot_managed_holding, order_execution_type, order_rate, signal_type="primary"
                            )
                            if sell_response and sell_response.get('error') == 0:
                                # Assuming full sell of managed holding
                                bot_managed_holding = 0.0 
                                last_trade_type = 'SELL'
                                print(f"Real primary sell SUCCESS. Bot now manages: {bot_managed_holding:.8f} {base_currency}.")
                            else:
                                print("Real primary sell order failed, not updating bot managed holding.")
                        else:
                            print("Not holding any bot-managed coins or already in 'CASH' state (from previous sell), skipping primary sell order.")
                    else:
                        print("No primary crossover detected in this update.")

                    # --- Backup Signal Logic (if no primary signal triggered) ---
                    # This logic ensures the bot attempts to provide a trade if its internal state
                    # (derived from MAs) is out of sync with its actual managed holding state,
                    # without a direct crossover signal. This might happen if the bot was stopped
                    # and restarted, or if there was a rapid price movement.
                    
                    # If current MA state is HOLDING but bot's last action was not BUY or bot has no managed holding
                    if derived_bot_state == "HOLDING" and (last_trade_type != 'BUY' or bot_managed_holding == 0.0):
                        print(f"!!! BACKUP BUY SIGNAL DETECTED !!! State changed from CASH to HOLDING without primary crossover.")
                        order_rate = None
                        if order_execution_type == 'limit':
                            order_rate = current_bitkub_ask_price * (1 + max_slippage_percentage / 100)
                            print(f"  Calculated backup buy limit rate with slippage: {order_rate:.{get_display_decimals(order_rate)}f}")
                        
                        buy_response = place_buy_order_bitkub(
                            bitkub_api_key, bitkub_api_secret, bitkub_symbol, position_size_thb, order_execution_type, order_rate, signal_type="backup"
                        )
                        if buy_response and buy_response.get('error') == 0:
                            received_coin = float(buy_response['result'].get('rec', 0.0))
                            bot_managed_holding += received_coin
                            last_trade_type = 'BUY'
                            print(f"Real backup buy SUCCESS. Bot now manages: {bot_managed_holding:.8f} {base_currency}.")
                        else:
                            print("Real backup buy order failed, not updating bot managed holding.")

                    # If current MA state is CASH but bot has managed holding and last action was not SELL
                    elif derived_bot_state == "CASH" and bot_managed_holding > 0 and last_trade_type != 'SELL':
                        print(f"!!! BACKUP SELL SIGNAL DETECTED !!! State changed from HOLDING to CASH without primary crossover.")
                        order_rate = None
                        if order_execution_type == 'limit':
                            order_rate = current_bitkub_bid_price * (1 - max_slippage_percentage / 100)
                            print(f"  Calculated backup sell limit rate with slippage: {order_rate:.{get_display_decimals(order_rate)}f}")
                        
                        sell_response = place_sell_order_bitkub(
                            bitkub_api_key, bitkub_api_secret, bitkub_symbol, bot_managed_holding, order_execution_type, order_rate, signal_type="backup"
                        )
                        if sell_response and sell_response.get('error') == 0:
                            bot_managed_holding = 0.0
                            last_trade_type = 'SELL'
                            print(f"Real backup sell SUCCESS. Bot now manages: {bot_managed_holding:.8f} {base_currency}.")
                        else:
                            print("Real backup sell order failed, not updating bot managed holding.")

                    # Update previous state for the next iteration
                    previous_derived_bot_state = derived_bot_state

                else:
                    print("Not enough MA data to check for crossovers or determine state.")
                    # If not enough data, previous_derived_bot_state remains UNKNOWN or its last valid state
            else:
                print("No data or MAs to display for this update. Retrying in next cycle.")

            # Refresh actual Bitkub balance to display (overall account balance)
            current_thb_balance = get_bitkub_balance(bitkub_api_key, bitkub_api_secret, quote_currency)
            current_coin_balance = get_bitkub_balance(bitkub_api_key, bitkub_api_secret, base_currency)

            print(f"Current Bitkub {quote_currency} balance: {current_thb_balance:.2f}")
            print(f"Current Bitkub {base_currency} balance: {current_coin_balance:.8f} (Total account balance)")
            print(f"Bot managed holding amount: {bot_managed_holding:.8f} {base_currency}")
            print(f"Last actual trade type: {last_trade_type}")
            print(f"Previous derived bot state for next cycle: {previous_derived_bot_state}")

            time.sleep(0.1) # Small delay before checking for the next candle close

        except Exception as e:
            print(f"An error occurred in monitoring loop: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    monitor_mas_on_candle_close()
