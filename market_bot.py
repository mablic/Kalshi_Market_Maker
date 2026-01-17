import os
import asyncio
import json
import time
import traceback
from incentive import INCENTIVE_PROGRAM
from trade import TRADE
from clients import KalshiHttpClient, Environment
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from datetime import datetime

TRADE_SIZE = 1
TRADE_DELTA = 0.01
WAIT_TIME = 60
EXPIRATION_TS = 1
TRADE_TICKER_SIZE = 2
LOG_FILE = "trade.log"
INCENTIVE_SIZE = 300

class MARKET_BOT:

    def __init__(self, incentive_program: INCENTIVE_PROGRAM, trade: TRADE, client: KalshiHttpClient):
        self.incentive_program = incentive_program
        self.trade = trade
        self.client = client
        self.trade.trade_size = TRADE_SIZE
        self.trade.trade_delta = TRADE_DELTA
        self.trade.expiration_ts = EXPIRATION_TS
        self.wait_time = WAIT_TIME
        self.log_file = LOG_FILE
        self.trade_ticker_size = TRADE_TICKER_SIZE
        self.trade.incentive_size = INCENTIVE_SIZE

    def get_datetime(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def log(self, message: str):
        """Print message to console and write to log file."""
        print(message)
        try:
            with open(self.log_file, 'a') as f:
                f.write(message + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def start_trading(self):
        try:
            curr_open_orders = self.client.get_open_orders()['orders']
            if curr_open_orders:
                for order in curr_open_orders:
                    try:
                        if order['status'] not in ['canceled', 'filled', 'executed']:
                            ticker = order.get('ticker', 'N/A')
                            side = order.get('side', 'N/A')
                            yes_price = order.get('yes_price_dollars', order.get('yes_price', 'N/A'))
                            no_price = order.get('no_price_dollars', order.get('no_price', 'N/A'))
                            price = yes_price if side == 'yes' else no_price
                            self.log(f"{self.get_datetime()} [CANCEL ORDER] Ticker: {ticker} | Side: {side} | Price: {price}")
                            self.client.cancel_open_order(order['order_id'])
                    except Exception as e:
                        self.log(f"{self.get_datetime()} [ERROR] Failed to cancel order: {str(e)}")
                        self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")
        
            curr_open_positions = self.client.get_positions()['market_positions']
            if curr_open_positions:
                for position in curr_open_positions:
                    try:
                        position_count = position.get('position', 0)
                        # Skip positions where position count is 0
                        if position_count == 0:
                            continue
                        
                        # Determine side: positive position = long yes, negative = long no
                        side = 'yes' if position_count > 0 else 'no'
                        count = abs(position_count)
                        
                        # Get order book to find current market price
                        order_book = self.client.get_market_ticker_order_book(position['ticker'])['orderbook']
                
                        # For market orders, use best bid price (highest price someone will pay)
                        # yes_dollars are bid prices for yes, no_dollars are bid prices for no
                        if side == 'yes':
                            # Get best bid price for yes (highest price)
                            yes_dollars = order_book.get('yes_dollars', [])
                            if yes_dollars:
                                best_bid = max(yes_dollars, key=lambda x: float(x[0]))
                                yes_price_dollars = f"{float(best_bid[0]):.4f}"
                            else:
                                yes_price_dollars = None
                            no_price_dollars = None
                        else:
                            # Get best bid price for no (highest price)
                            no_dollars = order_book.get('no_dollars', [])
                            if no_dollars:
                                best_bid = max(no_dollars, key=lambda x: float(x[0]))
                                no_price_dollars = f"{float(best_bid[0]):.4f}"
                            else:
                                no_price_dollars = None
                            yes_price_dollars = None
                        
                        if (side == 'yes' and yes_price_dollars is None) or (side == 'no' and no_price_dollars is None):
                            ticker = position.get('ticker', 'N/A')
                            position_count = position.get('position', 0)
                            self.log(f"{self.get_datetime()} [SKIP POSITION] Ticker: {ticker} | Position: {position_count} | Reason: No bid price available")
                            continue
                        
                        ticker = position.get('ticker', 'N/A')
                        price = yes_price_dollars if side == 'yes' else no_price_dollars
                        self.log(f"{self.get_datetime()} [CLOSE POSITION] Ticker: {ticker} | Side: {side} | Price: {price} | Count: {count}")
                        self.client.close_open_position_order(
                            ticker=position['ticker'],
                            side=side,
                            action='sell',
                            count=count,
                            type="limit",
                            yes_price_dollars=yes_price_dollars,
                            no_price_dollars=no_price_dollars,
                            time_in_force="immediate_or_cancel",
                            reduce_only=True,
                        )
                    except Exception as e:
                        ticker = position.get('ticker', 'N/A')
                        self.log(f"{self.get_datetime()} [ERROR] Failed to close position {ticker}: {str(e)}")
                        self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")

            curr_open_positions = self.client.get_positions()['market_positions']
            
            # Check if there are any actual positions (non-zero position counts)
            actual_positions = [p for p in curr_open_positions if p.get('position', 0) != 0] if curr_open_positions else []
            if actual_positions:
                position_info = []
                for pos in actual_positions:
                    ticker = pos.get('ticker', 'N/A')
                    position_count = pos.get('position', 0)
                    side = 'yes' if position_count > 0 else 'no'
                    position_info.append(f"{ticker}({side}:{abs(position_count)})")
                self.log(f"{self.get_datetime()} [SKIP TRADING] Open positions: {', '.join(position_info)}")
                return

            curr_traded_incentive = self.incentive_program.get_trade_incentive_dict()
            if not curr_traded_incentive:
                try:
                    self.log(f"{self.get_datetime()} [NEW SESSION] Starting new trading session")
                    curr_market_incentive = self.client.get_market_incentive()
                    self.incentive_program.load_market_incentive(curr_market_incentive['incentive_programs'])
                    incentive_tickers = self.incentive_program.get_open_incentive_tickers()
                    ticker_dict = {}
                    for ticker in incentive_tickers:
                        curr_market_ticker = self.client.get_market_ticker(ticker)
                        ticker_dict[ticker] = curr_market_ticker['market']
                    self.incentive_program.fill_incentive_tickers(ticker_dict)
                    self.incentive_program.prepare_trade_incentive(self.trade_ticker_size)
                    curr_traded_incentive = self.incentive_program.get_trade_incentive_dict()
                    # Format incentive info
                    incentive_summary = []
                    for ticker, data in curr_traded_incentive.items():
                        yes_price = data.get('yes_ask_dollars', 'N/A')
                        no_price = data.get('no_ask_dollars', 'N/A')
                        reward = data.get('period_reward', 0) / 100 if data.get('period_reward') else 0
                        incentive_summary.append(f"{ticker}(Y:{yes_price},N:{no_price},Reward:${reward:.2f})")
                    self.log(f"{self.get_datetime()} [NEW INCENTIVE] Trading tickers: {', '.join(incentive_summary)}")
                    self.place_order(curr_traded_incentive)
                except Exception as e:
                    self.log(f"{self.get_datetime()} [ERROR] Failed to start new trading session: {str(e)}")
                    self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")
            else:
                try:
                    # Format existing incentive info
                    incentive_summary = []
                    for ticker, data in curr_traded_incentive.items():
                        yes_price = data.get('yes_ask_dollars', 'N/A')
                        no_price = data.get('no_ask_dollars', 'N/A')
                        incentive_summary.append(f"{ticker}(Y:{yes_price},N:{no_price})")
                    self.log(f"{self.get_datetime()} [UPDATE INCENTIVE] Existing tickers: {', '.join(incentive_summary)}")
                    curr_traded_incentive = self.incentive_program.get_trade_incentive_dict()
                    incentive_tickers = self.incentive_program.get_trade_ticker()
                    ticker_dict = {}
                    for ticker in incentive_tickers:
                        curr_market_ticker = self.client.get_market_ticker(ticker)
                        ticker_dict[ticker] = curr_market_ticker['market']
                    curr_traded_incentive = self.incentive_program.update_trade_incentive_dict(ticker_dict)
                    if curr_traded_incentive:
                        incentive_summary = []
                        for ticker, data in curr_traded_incentive.items():
                            yes_price = data.get('yes_ask_dollars', 'N/A')
                            no_price = data.get('no_ask_dollars', 'N/A')
                            incentive_summary.append(f"{ticker}(Y:{yes_price},N:{no_price})")
                        self.log(f"{self.get_datetime()} [UPDATE INCENTIVE] Updated tickers: {', '.join(incentive_summary)}")
                        self.place_order(curr_traded_incentive)
                    else:
                        self.log(f"{self.get_datetime()} [NEW SESSION] No existing incentive, starting new trading session")
                        curr_market_incentive = self.client.get_market_incentive()
                        self.incentive_program.load_market_incentive(curr_market_incentive['incentive_programs'])
                        incentive_tickers = self.incentive_program.get_open_incentive_tickers()
                        ticker_dict = {}
                        for ticker in incentive_tickers:
                            curr_market_ticker = self.client.get_market_ticker(ticker)
                            ticker_dict[ticker] = curr_market_ticker['market']
                        self.incentive_program.fill_incentive_tickers(ticker_dict)
                        self.incentive_program.prepare_trade_incentive(self.trade_ticker_size)
                        curr_traded_incentive = self.incentive_program.get_trade_incentive_dict()
                        incentive_summary = []
                        for ticker, data in curr_traded_incentive.items():
                            yes_price = data.get('yes_ask_dollars', 'N/A')
                            no_price = data.get('no_ask_dollars', 'N/A')
                            reward = data.get('period_reward', 0) / 100 if data.get('period_reward') else 0
                            incentive_summary.append(f"{ticker}(Y:{yes_price},N:{no_price},Reward:${reward:.2f})")
                        self.log(f"{self.get_datetime()} [NEW INCENTIVE] Trading tickers: {', '.join(incentive_summary)}")
                        self.place_order(curr_traded_incentive)
                except Exception as e:
                    self.log(f"{self.get_datetime()} [ERROR] Failed to update incentive: {str(e)}")
                    self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")
        except Exception as e:
            self.log(f"{self.get_datetime()} [ERROR] Critical error in start_trading: {str(e)}")
            self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")
    
    def place_order(self, curr_traded_incentive: dict):
        for trade_ticker in curr_traded_incentive:
            try:
                order_book = self.client.get_market_ticker_order_book(trade_ticker)['orderbook']
                # Format top 5 best prices for Yes and No
                yes_prices = sorted(order_book.get('yes_dollars', []), key=lambda x: -float(x[0]))[:5]
                no_prices = sorted(order_book.get('no_dollars', []), key=lambda x: -float(x[0]))[:5]
                
                yes_book_str = ' | '.join([f"${float(p[0]):.4f} x {p[1]}" for p in yes_prices])
                no_book_str = ' | '.join([f"${float(p[0]):.4f} x {p[1]}" for p in no_prices])
                
                self.log(f"{self.get_datetime()} [ORDER BOOK] Ticker: {trade_ticker}")
                self.log(f"  └─ Yes (Top 5): {yes_book_str}")
                self.log(f"  └─ No (Top 5):  {no_book_str}")
                self.trade.get_balance(self.client.get_balance()['balance'])
                # self.trade.get_balance(1000)
                market_orders = []
                try:
                    yes_order = self.trade.create_open_order(trade_ticker, curr_traded_incentive[trade_ticker], order_book, 'yes')
                except Exception as e:
                    self.log(f"{self.get_datetime()} [ERROR] Failed to create yes order for {trade_ticker}: {str(e)}")
                    yes_order = None
                
                try:
                    no_order = self.trade.create_open_order(trade_ticker, curr_traded_incentive[trade_ticker], order_book, 'no')
                except Exception as e:
                    self.log(f"{self.get_datetime()} [ERROR] Failed to create no order for {trade_ticker}: {str(e)}")
                    no_order = None
                
                if yes_order and no_order:
                    market_orders.append(yes_order)
                    market_orders.append(no_order)
                    
                for order in market_orders:
                    if order:
                        try:
                            ticker = order.get('ticker', 'N/A')
                            side = order.get('side', 'N/A')
                            action = order.get('action', 'N/A')
                            count = order.get('count', 0)
                            order_type = order.get('type', 'N/A')
                            yes_price = order.get('yes_price_dollars', None)
                            no_price = order.get('no_price_dollars', None)
                            price = yes_price if side == 'yes' else no_price
                            
                            self.log(f"{self.get_datetime()} [OPEN ORDER] Ticker: {ticker} | Side: {side} | Action: {action} | Count: {count} | Type: {order_type} | Price: {price}")
                            
                            response = self.client.create_open_order(
                                ticker=order['ticker'],
                                side=order['side'],
                                action=order['action'],
                                count=order['count'],
                                type=order['type'],
                                yes_price_dollars= order['yes_price_dollars'] if 'yes_price_dollars' in order else None,
                                no_price_dollars= order['no_price_dollars'] if 'no_price_dollars' in order else None,
                                expiration_ts=order['expiration_ts'],
                            )
                            
                            # Format response
                            if response and 'order' in response:
                                resp_order = response['order']
                                order_id = resp_order.get('order_id', 'N/A')
                                status = resp_order.get('status', 'N/A')
                                fill_count = resp_order.get('fill_count', 0)
                                remaining = resp_order.get('remaining_count', 0)
                                self.log(f"{self.get_datetime()} [ORDER RESPONSE] OrderID: {order_id[:8]}... | Status: {status} | Filled: {fill_count} | Remaining: {remaining}")
                            else:
                                self.log(f"{self.get_datetime()} [ORDER RESPONSE] {response}")
                        except Exception as e:
                            ticker = order.get('ticker', 'N/A')
                            error_msg = str(e)
                            
                            # Try to extract API error details if it's an HTTPError
                            if hasattr(e, 'response') and hasattr(e.response, '_error_details'):
                                api_error = e.response._error_details
                                error_msg += f" | API Error: {api_error}"
                            elif "API Error Response" in str(e):
                                # Fallback: extract from error message if available
                                pass
                            
                            self.log(f"{self.get_datetime()} [ERROR] Failed to place order for {ticker}: {error_msg}")
                            
                            # Log order details for debugging
                            self.log(f"{self.get_datetime()} [ERROR] Order details: Ticker={ticker}, Side={side}, Action={action}, Count={count}, Type={order_type}, Price={price}")
                            self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")
            except Exception as e:
                self.log(f"{self.get_datetime()} [ERROR] Failed to process order for {trade_ticker}: {str(e)}")
                self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")

    def run(self):
        """Main trading loop with error handling - keeps running even if errors occur."""
        while True:
            try:
                self.start_trading()
            except KeyboardInterrupt:
                self.log(f"{self.get_datetime()} [SHUTDOWN] Received interrupt signal, shutting down gracefully")
                raise  # Re-raise to allow clean shutdown
            except Exception as e:
                self.log(f"{self.get_datetime()} [ERROR] Unhandled error in main loop: {str(e)}")
                self.log(f"{self.get_datetime()} [ERROR] Traceback: {traceback.format_exc()}")
                self.log(f"{self.get_datetime()} [INFO] Continuing to next iteration in {self.wait_time} seconds...")
            finally:
                time.sleep(self.wait_time)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    env = Environment.PROD # toggle environment here
    KEYID = os.getenv('DEMO_KEYID') if env == Environment.DEMO else os.getenv('PROD_KEYID')
    KEYFILE = os.getenv('DEMO_KEYFILE') if env == Environment.DEMO else os.getenv('PROD_KEYFILE')

    try:
        with open(KEYFILE, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None  # Provide the password if your key is encrypted
            )
    except FileNotFoundError:
        raise FileNotFoundError(f"Private key file not found at {KEYFILE}")
    except Exception as e:
        raise Exception(f"Error loading private key: {str(e)}")

    # Initialize the HTTP client
    client = KalshiHttpClient(
        key_id=KEYID,
        private_key=private_key,
        environment=env
    )

    incentive_program = INCENTIVE_PROGRAM()
    trade = TRADE()
    market_bot = MARKET_BOT(incentive_program, trade, client)
    market_bot.run()


