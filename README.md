# Kalshi Market Making Bot

An automated trading bot for market making on the Kalshi prediction market exchange. The bot participates in incentive programs by placing liquidity orders on selected markets.

## Overview

This bot automates the process of:

- Monitoring and participating in Kalshi incentive programs
- Placing limit orders to provide liquidity on selected markets
- Managing open positions and orders
- Logging all trading activities for monitoring and analysis

## Features

- **Automated Trading**: Automatically places limit orders based on incentive programs
- **Position Management**: Closes open positions and cancels existing orders before new trading sessions
- **Incentive Tracking**: Monitors and tracks incentive programs, updating trading strategies accordingly
- **Error Handling**: Robust error handling with automatic retry on transient failures
- **Comprehensive Logging**: Detailed logs of all trading activities written to `trade.log`
- **Dual Environment Support**: Works with both DEMO and PROD environments

## Requirements

- Python 3.8+
- Kalshi API credentials (API Key ID and Private Key)
- Virtual environment (recommended)

## Installation

1. **Clone the repository** (if applicable):

```bash
git clone <repository-url>
cd KalshiModel
```

2. **Create and activate a virtual environment**:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Demo Environment
DEMO_KEYID=your_demo_api_key_id
DEMO_KEYFILE=/path/to/demo_private_key.pem

# Production Environment
PROD_KEYID=your_prod_api_key_id
PROD_KEYFILE=/path/to/prod_private_key.pem
```

### Trading Parameters

Edit the constants in `market_bot.py` to customize trading behavior:

```python
TRADE_SIZE = 1              # Number of contracts per order
TRADE_DELTA = 0.01          # Price delta for order placement
WAIT_TIME = 60              # Seconds between trading cycles
EXPIRATION_TS = 1           # Order expiration time in minutes
TRADE_TICKER_SIZE = 2       # Number of tickers to trade simultaneously
INCENTIVE_SIZE = 300        # Incentive size parameter
```

### Environment Selection

In `market_bot.py`, change the environment:

```python
env = Environment.PROD  # Use Environment.DEMO for testing
```

## Usage

### Running the Bot

```bash
python market_bot.py
```

The bot will:

1. Cancel any existing open orders
2. Close any open positions
3. Check for available incentive programs
4. Place new orders based on incentives
5. Wait `WAIT_TIME` seconds before repeating

### Stopping the Bot

Press `Ctrl+C` to stop the bot gracefully. The bot will log a shutdown message and exit.

## Project Structure

```
KalshiModel/
├── market_bot.py      # Main bot logic and trading loop
├── clients.py         # Kalshi API client implementation
├── incentive.py       # Incentive program tracking and management
├── trade.py           # Order creation and trading logic
├── main.py            # Alternative entry point (if used)
├── requirements.txt   # Python dependencies
├── trade.log          # Trading activity logs (auto-generated)
└── .env               # Environment variables (not in repo)
```

## Key Components

### MARKET_BOT (`market_bot.py`)

Main bot class that orchestrates the trading workflow:

- `start_trading()`: Main trading cycle
- `place_order()`: Places orders for incentive tickers
- `run()`: Main loop with error handling
- `log()`: Unified logging to console and file

### KalshiHttpClient (`clients.py`)

API client for interacting with Kalshi:

- Authentication with RSA signatures
- Rate limiting
- Order management (create, cancel, get orders)
- Position management
- Market data retrieval

### INCENTIVE_PROGRAM (`incentive.py`)

Manages incentive program tracking:

- Loads market incentives
- Filters and selects tradable incentives
- Updates incentive status
- Maintains trade incentive dictionary

### TRADE (`trade.py`)

Order creation logic:

- Calculates order prices based on order book
- Creates limit orders with proper pricing
- Manages trade size and balance

## Logging

All trading activities are logged to `trade.log` with timestamps. Log entries include:

- **Order Operations**: Cancel, open, and close orders with details
- **Position Management**: Open positions, closing positions
- **Order Books**: Top 5 best prices for Yes/No sides
- **API Responses**: Order status, fills, and remaining quantities
- **Errors**: Detailed error messages with tracebacks
- **Trading Sessions**: New/updated incentives and tickers

Example log entries:

```
2026-01-16 18:05:57 [CANCEL ORDER] Ticker: KXHIGHCHI-26JAN16-B35.5 | Side: yes | Price: 0.4600
2026-01-16 18:05:57 [CLOSE POSITION] Ticker: KXHIGHCHI-26JAN16-B35.5 | Side: no | Price: 0.4600 | Count: 1
2026-01-16 18:05:58 [OPEN ORDER] Ticker: KXLOWTMIA-26JAN17-B60.5 | Side: yes | Action: buy | Count: 1 | Type: limit | Price: 0.5300
```

## Error Handling

The bot includes comprehensive error handling:

- **Transient Errors**: 503 Service Unavailable errors are logged and retried on next cycle
- **Client Errors**: 400 Bad Request errors are logged with detailed API error messages
- **Critical Errors**: All exceptions are caught, logged with full tracebacks, and the bot continues running
- **Graceful Shutdown**: KeyboardInterrupt is handled for clean shutdown

## Important Notes

⚠️ **Risk Warning**:

- This bot trades real money when using PROD environment
- Always test thoroughly in DEMO environment first
- Monitor `trade.log` regularly for errors
- Ensure sufficient account balance for trading

📝 **Best Practices**:

- Start with `WAIT_TIME=60` or higher to avoid rate limiting
- Monitor `trade.log` for the first few hours of operation
- Keep API keys secure and never commit them to version control
- Use `.env` file for credentials (already in `.gitignore`)

🔧 **Troubleshooting**:

- **503 Errors**: API server temporarily unavailable - bot will retry automatically
- **400 Errors**: Check order parameters in logs (price format, required fields)
- **401 Errors**: Verify API credentials in `.env` file
- **429 Errors**: Reduce trading frequency (increase `WAIT_TIME`)

## API Documentation

For detailed API documentation, refer to:

- [Kalshi API Documentation](https://docs.kalshi.com/api-reference/)

## License

[Specify your license here]

## Disclaimer

This software is provided as-is for educational and research purposes. Trading involves risk of loss. Use at your own risk.
