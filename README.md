# BitkubBot

A Python trading bot for monitoring moving average crossovers and simulating trades on Bitkub using Binance price data.

## Features
- Supports SMA, EMA, and WMA crossovers
- Configurable trading pair, position size, and indicator settings
- Simulates buy/sell orders (mock trading)
- Loads configuration from `config.json` or interactively creates one
- Monitors at user-defined candle intervals (e.g., 1m, 1h, 1d)

## Requirements
- Python 3.8+
- pip (Python package manager)

### Python Dependencies
- requests
- python-binance

Install dependencies with:
```bash
pip install requests python-binance
```

## Setup
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd BitkubTrendTrader
   ```
2. **Install dependencies**
   ```bash
   pip install requests python-binance
   ```
3. **Set Binance API keys** (for price data)
   - Set environment variables:
     ```bash
     export BINANCE_API_KEY=your_api_key
     export BINANCE_API_SECRET=your_api_secret
     ```
   - Or set them in your shell profile (e.g., `.bashrc`)

4. **Configure the bot**
   - On first run, the bot will prompt you for trading pair, position size, indicator settings, etc., and save them to `config.json`.
   - You can edit `config.json` later to change settings.

## Running the Bot

```bash
python BitkubBot.py
```

- The bot will monitor the specified trading pair and interval, print moving average values, and simulate trades based on crossover signals.
- All trades are mock/simulated (no real orders are placed).

## Configuration Options
- **bitkub_symbol**: Trading pair on Bitkub (e.g., `THB_BTC`)
- **binance_symbol**: Trading pair on Binance (e.g., `BTCUSDT`)
- **position_size_thb**: Amount of THB to use per trade
- **trading_fee_percentage**: Trading fee as a percentage (e.g., 0.25 for 0.25%)
- **indicator_settings**: Fast/slow MA periods and type (SMA, EMA, WMA)
- **timeframe**: Candle interval (e.g., 1m, 1h, 1d)
- **self_buy_enabled**: Start with a mock holding
- **self_buy_amount_coin**: Amount of coin to start with if self-buy is enabled

## Notes
- This bot is for educational and research purposes only.
- No real trading is performed; all trades are simulated.
- You must have a working internet connection to fetch price data.

## License
MIT License
