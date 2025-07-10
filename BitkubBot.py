import os
import time
import requests
import json # New import for JSON handling
from binance.client import Client
from datetime import datetime, timedelta

# --- Configuration File Name ---
CONFIG_FILE = 'config.json'

# --- Helper Functions ---
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
        client (binance.client.Client): The initialized Binance client.
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
        klines = client.get_klines(symbol=symbol, interval=binance_interval, limit=fetch_limit)

        if not klines:
            print(f"No klines data fetched for {symbol} with interval {interval}.")
            return {'close_prices': [], 'current_confirmed_mas': {}, 'previous_confirmed_mas': {}}

        close_prices = []
        for kline in klines:
            close_price = float(kline[4])
            close_prices.append(close_price)

        # Ensure we have enough data for both current and previous confirmed MAs
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

def get_binance_price(client, symbol):
    """Fetches the current ticker price for a given symbol from Binance."""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"Error fetching price for {symbol} from Binance: {e}")
        return None

def get_bitkub_price(symbol):
    """Fetches the current ticker price for a given symbol from Bitkub."""
    try:
        url = f"https://api.bitkub.com/api/market/ticker?sym={symbol}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if symbol in data and 'last' in data[symbol]:
            return float(data[symbol]['last'])
        else:
            print(f"Error: Symbol '{symbol}' not found in Bitkub ticker response or 'last' price missing.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price for {symbol} from Bitkub API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching Bitkub price for {symbol}: {e}")
        return None

def place_buy_order_bitkub_mock(bitkub_symbol, amount_thb, binance_client, binance_trading_pair_usdt, trading_fee_percentage, signal_type="primary"):
    """
    Mocks a buy order on Bitkub, calculating received coin amount based on Binance and Bitkub prices.

    Args:
        bitkub_symbol (str): The trading pair on Bitkub (e.g., 'THB_HYPER').
        amount_thb (float): The amount of THB to spend.
        binance_client (binance.client.Client): The initialized Binance client.
        binance_trading_pair_usdt (str): The corresponding USDT pair on Binance (e.g., 'HYPERUSDT').
        trading_fee_percentage (float): The trading fee as a decimal (e.g., 0.0025 for 0.25%).
        signal_type (str): 'primary' or 'backup' to indicate the signal source.

    Returns:
        float: The mock amount of coin received, or 0 if the order fails.
    """
    print(f"MOCK BUY ({signal_type.upper()} SIGNAL): Attempting to buy {bitkub_symbol} with {amount_thb} THB...")

    usdt_thb_price = get_bitkub_price('THB_USDT') 
    coin_usdt_price = get_binance_price(binance_client, binance_trading_pair_usdt)

    if usdt_thb_price is None or coin_usdt_price is None or coin_usdt_price == 0:
        print("MOCK BUY FAILED: Could not get necessary prices for calculation (USDT/THB from Bitkub or Coin/USDT from Binance).")
        return 0

    amount_usdt = amount_thb / usdt_thb_price
    coin_amount_before_fees = amount_usdt / coin_usdt_price
    coin_amount_received = coin_amount_before_fees * (1 - trading_fee_percentage)

    print(f"MOCK BUY SUCCESS: Spent {amount_thb} THB, received {coin_amount_received:.8f} {bitkub_symbol.split('_')[1]} (after {trading_fee_percentage*100:.2f}% fee).")
    return coin_amount_received

def place_sell_order_bitkub_mock(bitkub_symbol, coin_amount, binance_client, binance_trading_pair_usdt, trading_fee_percentage, signal_type="primary"):
    """
    Mocks a sell order on Bitkub.

    Args:
        bitkub_symbol (str): The trading pair on Bitkub (e.g., 'THB_HYPER').
        coin_amount (float): The amount of coin to sell.
        binance_client (binance.client.Client): The initialized Binance client.
        binance_trading_pair_usdt (str): The corresponding USDT pair on Binance (e.g., 'HYPERUSDT').
        trading_fee_percentage (float): The trading fee as a decimal (e.g., 0.0025 for 0.25%).
        signal_type (str): 'primary' or 'backup' to indicate the signal source.

    Returns:
        bool: True if the mock order is successful, False otherwise.
    """
    print(f"MOCK SELL ({signal_type.upper()} SIGNAL): Attempting to sell {coin_amount:.8f} {bitkub_symbol.split('_')[1]}...")

    usdt_thb_price = get_bitkub_price('THB_USDT')
    coin_usdt_price = get_binance_price(binance_client, binance_trading_pair_usdt)

    if usdt_thb_price is None or coin_usdt_price is None:
        print("MOCK SELL (REPORTING) FAILED: Could not get necessary prices for calculation (USDT/THB from Bitkub or Coin/USDT from Binance).")
        return False

    mock_thb_received_before_fees_usdt = coin_amount * coin_usdt_price
    mock_thb_received_before_fees_thb = mock_thb_received_before_fees_usdt * usdt_thb_price
    mock_thb_received_after_fees = mock_thb_received_before_fees_thb * (1 - trading_fee_percentage)

    print(f"MOCK SELL SUCCESS: Sold {coin_amount:.8f} {bitkub_symbol.split('_')[1]}, would receive approx. {mock_thb_received_after_fees:.2f} THB (after {trading_fee_percentage*100:.2f}% fee).")
    return True

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

    config['bitkub_symbol'] = input("Enter Coin to trade in Bitkub format (e.g., THB_HYPER): ").strip().upper()
    config['binance_symbol'] = input("Enter Coin to monitor in Binance format (e.g., HYPERUSDT): ").strip().upper()

    while True:
        try:
            config['position_size_thb'] = float(input("Enter default position size in THB (e.g., 100): "))
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
        indicator_type = input("Enter type of indicator (SMA, EMA, WMA, default SMA): ").strip().upper() or "SMA"
        if indicator_type in ['SMA', 'EMA', 'WMA']:
            indicator_settings['indicator_type'] = indicator_type
            break
        else:
            print("Invalid indicator type. Please choose from SMA, EMA, or WMA.")
    config['indicator_settings'] = indicator_settings

    while True:
        timeframe = input("Enter timeframe (e.g., 1s, 1m, 1h, 1d, default 1d for production, 1s for testing): ").strip() or "1d"
        # Basic validation for common intervals, can be expanded
        if timeframe in ['1s', '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']:
            config['timeframe'] = timeframe
            break
        else:
            print("Invalid timeframe. Please enter a valid interval (e.g., 1s, 1m, 1d).")

    while True:
        self_buy_enabled_str = input("Enable self-buy at startup? (true/false, default false): ").strip().lower() or "false"
        if self_buy_enabled_str in ['true', 'false']:
            config['self_buy_enabled'] = self_buy_enabled_str == 'true'
            break
        else:
            print("Invalid input. Please enter 'true' or 'false'.")

    config['self_buy_amount_coin'] = 0.0
    if config['self_buy_enabled']:
        while True:
            try:
                config['self_buy_amount_coin'] = float(input("Enter self-buy amount in coin unit (e.g., 0.001): "))
                if config['self_buy_amount_coin'] < 0:
                    raise ValueError("Self-buy amount cannot be negative.")
                break
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter a non-negative number.")

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Configuration saved to {CONFIG_FILE}.")
    return config

def monitor_mas_on_candle_close():
    """
    Monitors cryptocurrency price data and calculates MAs, updating after each candle close.
    Detects MA crossovers, prints signals, reports derived bot state, and performs mock trades.
    Settings are loaded from config.json.
    """
    config = load_config()

    binance_symbol = config['binance_symbol']
    bitkub_symbol = config['bitkub_symbol']
    position_size_thb = config['position_size_thb']
    trading_fee_percentage = config['trading_fee_percentage']
    fast_ma_period = config['indicator_settings']['fast_ma_period']
    slow_ma_period = config['indicator_settings']['slow_ma_period']
    ma_type = config['indicator_settings']['indicator_type']
    interval = config['timeframe']
    self_buy_enabled = config['self_buy_enabled']
    self_buy_amount_coin = config['self_buy_amount_coin']

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

    # Initialize Binance client
    binance_client = Client(os.environ.get('BINANCE_API_KEY', ''), os.environ.get('BINANCE_API_SECRET', ''))

    # Mock trading state variables
    current_holding_amount = 0.0
    last_trade_type = None
    previous_derived_bot_state = "UNKNOWN"

    # Apply self-buy at startup if enabled
    if self_buy_enabled and self_buy_amount_coin > 0:
        current_holding_amount = self_buy_amount_coin
        last_trade_type = 'BUY'
        print(f"Self-buy enabled: Bot starts with {current_holding_amount:.8f} {bitkub_symbol.split('_')[1]} (mock holding).")
    else:
        print(f"Initial mock holding amount: {current_holding_amount:.8f} {bitkub_symbol.split('_')[1]}")
    
    print(f"Initial last trade type: {last_trade_type}")
    print(f"Initial previous derived bot state: {previous_derived_bot_state}")


    while True:
        try:
            # Get current Unix timestamp in milliseconds
            current_unix_ms = int(time.time() * 1000)
            interval_duration_ms = duration_sec * 1000

            # Calculate the start time of the *current* interval
            current_interval_start_ms = (current_unix_ms // interval_duration_ms) * interval_duration_ms

            # Calculate the expected close time of the *current* interval
            expected_current_candle_close_ms = current_interval_start_ms + interval_duration_ms - 1

            # Calculate the expected close time of the *next* interval
            next_candle_close_time_ms = expected_current_candle_close_ms + interval_duration_ms

            # Calculate time to wait until the next candle is expected to close
            time_to_wait_ms = next_candle_close_time_ms - current_unix_ms

            if time_to_wait_ms > 0:
                print(f"Waiting {time_to_wait_ms / 1000:.2f} seconds for the next {interval} candle to close...")
                time.sleep(time_to_wait_ms / 1000)
            else:
                print(f"Already past expected {interval} candle close time, fetching immediately.")

            # Now that the candle should have closed, fetch the data and calculate MAs
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
                    print(f"Latest confirmed close price: {latest_confirmed_price:.{decimals}f}")
                else:
                    print("Not enough close price data for latest confirmed price.")

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

                    # Flag to check if a primary signal was triggered in this cycle
                    primary_signal_triggered = False

                    # Check for Primary Buy Signal
                    if fast_ma_current > slow_ma_current and fast_ma_previous <= slow_ma_previous:
                        print(f"!!! PRIMARY BUY SIGNAL DETECTED !!! {fast_ma_period}-{interval} {ma_type} crossed ABOVE {slow_ma_period}-{interval} {ma_type}.")
                        primary_signal_triggered = True
                        if last_trade_type != 'BUY':
                            mock_amount_received = place_buy_order_bitkub_mock(
                                bitkub_symbol, position_size_thb, binance_client, binance_symbol, trading_fee_percentage, signal_type="primary"
                            )
                            if mock_amount_received > 0:
                                current_holding_amount = mock_amount_received
                                last_trade_type = 'BUY'
                            else:
                                print("Mock primary buy order failed, not updating holding amount.")
                        else:
                            print("Already in a 'HOLDING' state (from previous buy), skipping primary mock buy order.")

                    # Check for Primary Sell Signal
                    elif fast_ma_current < slow_ma_current and fast_ma_previous >= slow_ma_previous:
                        print(f"!!! PRIMARY SELL SIGNAL DETECTED !!! {fast_ma_period}-{interval} {ma_type} crossed BELOW {slow_ma_period}-{interval} {ma_type}.")
                        primary_signal_triggered = True
                        if current_holding_amount > 0 and last_trade_type != 'SELL':
                            mock_sell_success = place_sell_order_bitkub_mock(
                                bitkub_symbol, current_holding_amount, binance_client, binance_symbol, trading_fee_percentage, signal_type="primary"
                            )
                            if mock_sell_success:
                                current_holding_amount = 0.0
                                last_trade_type = 'SELL'
                            else:
                                print("Mock primary sell order failed, not updating holding amount.")
                        else:
                            print("Not holding any coins or already in 'CASH' state (from previous sell), skipping primary mock sell order.")
                    else:
                        print("No primary crossover detected in this update.")

                    # --- Backup Signal Logic ---
                    if not primary_signal_triggered and previous_derived_bot_state != "UNKNOWN":
                        if derived_bot_state == "HOLDING" and previous_derived_bot_state == "CASH":
                            print(f"!!! BACKUP BUY SIGNAL DETECTED !!! State changed from CASH to HOLDING without primary crossover.")
                            if last_trade_type != 'BUY':
                                mock_amount_received = place_buy_order_bitkub_mock(
                                    bitkub_symbol, position_size_thb, binance_client, binance_symbol, trading_fee_percentage, signal_type="backup"
                                )
                                if mock_amount_received > 0:
                                    current_holding_amount = mock_amount_received
                                    last_trade_type = 'BUY'
                                else:
                                    print("Mock backup buy order failed, not updating holding amount.")
                            else:
                                print("Already in a 'HOLDING' state (from previous buy), skipping backup mock buy order.")

                        elif derived_bot_state == "CASH" and previous_derived_bot_state == "HOLDING":
                            print(f"!!! BACKUP SELL SIGNAL DETECTED !!! State changed from HOLDING to CASH without primary crossover.")
                            if current_holding_amount > 0 and last_trade_type != 'SELL':
                                mock_sell_success = place_sell_order_bitkub_mock(
                                    bitkub_symbol, current_holding_amount, binance_client, binance_symbol, trading_fee_percentage, signal_type="backup"
                                )
                                if mock_sell_success:
                                    current_holding_amount = 0.0
                                    last_trade_type = 'SELL'
                                else:
                                    print("Mock backup sell order failed, not updating holding amount.")
                            else:
                                print("Not holding any coins or already in 'CASH' state (from previous sell), skipping backup mock sell order.")

                    # Update previous state for the next iteration
                    previous_derived_bot_state = derived_bot_state

                else:
                    print("Not enough MA data to check for crossovers or determine state.")
                    # If not enough data, previous_derived_bot_state remains UNKNOWN or its last valid state
            else:
                print("No data or MAs to display for this update. Retrying in next cycle.")

            print(f"Current mock holding amount: {current_holding_amount:.8f} {bitkub_symbol.split('_')[1]}")
            print(f"Last mock trade type: {last_trade_type}")
            print(f"Previous derived bot state for next cycle: {previous_derived_bot_state}")

            time.sleep(0.1)

        except Exception as e:
            print(f"An error occurred in monitoring loop: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    monitor_mas_on_candle_close()
