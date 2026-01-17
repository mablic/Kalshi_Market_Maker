from datetime import datetime, timedelta

class INCENTIVE_PROGRAM:

    @staticmethod
    def _parse_iso_datetime(date_str: str) -> datetime:
        """Parse ISO 8601 datetime string, handling 'Z' timezone indicator."""
        # Replace 'Z' with '+00:00' for UTC timezone
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str)

    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(INCENTIVE_PROGRAM, cls).__new__(cls)
            cls.__instance.trade_incentive_dict = {}
        return cls.__instance

    def load_market_incentive(self, open_incentive_dict: dict):
        self.open_incentive_dict = {}
        self.open_incentive_dict = open_incentive_dict

    def get_open_incentive_tickers(self):
        if not self.open_incentive_dict:
            raise ValueError("Trade self.open_incentive_dict is not set")
        
        ticker_list = []
        for incentive in self.open_incentive_dict:
            ticker_list.append(incentive['market_ticker'])
        return ticker_list

    def fill_incentive_tickers(self, ticker_dict: dict):
        # ticker_dict in market key.
        self.incentive_tickers_dict = {}

        try:
            for incentive in self.open_incentive_dict:
                if incentive['market_ticker'] in ticker_dict:
                    end_date = self._parse_iso_datetime(incentive['end_date'])
                    # Convert to naive datetime for comparison if timezone-aware
                    end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
                    # Allow 5 minutes leeway for the timestamp comparison
                    curr_date_time = datetime.now() - timedelta(minutes=5)
                    if incentive['paid_out'] == False and end_date_naive > curr_date_time:
                        curr_ticker = incentive['market_ticker']
                        if float(ticker_dict[curr_ticker]['yes_ask_dollars']) >= 0.7 or float(ticker_dict[curr_ticker]['no_ask_dollars']) >= 0.7:
                            continue
                        else:
                            if incentive['target_size'] is None or ticker_dict[curr_ticker]['yes_ask_dollars'] is None or ticker_dict[curr_ticker]['no_ask_dollars'] is None or ticker_dict[curr_ticker]['notional_value_dollars'] is None or ticker_dict[curr_ticker]['volume'] is None:
                                continue
                            else:
                                yes_ask_dollars = float(ticker_dict[curr_ticker]['yes_ask_dollars'])
                                no_ask_dollars = float(ticker_dict[curr_ticker]['no_ask_dollars'])
                                notional_value_dollars = float(ticker_dict[curr_ticker]['notional_value_dollars'])
                                volume = float(ticker_dict[curr_ticker]['volume'])
                                spread = abs(yes_ask_dollars - no_ask_dollars)
                                max_loss_dollars = (yes_ask_dollars + no_ask_dollars - notional_value_dollars) * float(incentive['target_size'])
                                tmp_dict = {
                                    'ticker': curr_ticker,
                                    'start_date': incentive['start_date'],
                                    'discount_factor_bps': incentive['discount_factor_bps'],
                                    'end_date': incentive['end_date'],
                                    'id': incentive['id'],
                                    'incentive_type': incentive['incentive_type'],
                                    'paid_out': incentive['paid_out'],
                                    'period_reward': incentive['period_reward'],
                                    'target_size': incentive['target_size'],
                                    'yes_ask_dollars': yes_ask_dollars,
                                    'no_ask_dollars': no_ask_dollars,
                                    'notional_value_dollars': notional_value_dollars,
                                    'volume': volume,
                                    'spread': spread,
                                    'max_loss_dollars': max_loss_dollars
                                }
                                self.incentive_tickers_dict[incentive['market_ticker']] = tmp_dict
        except Exception as e:
            print(f"Error get_incentive_tickers tickers on the [INCENTIVE_PROGRAM]: {e}")
        finally:
            pass

    def prepare_trade_incentive(self, trade_ticker_size: int = 1):

        if not self.incentive_tickers_dict:
            raise ValueError("Incentive dictionary or ticker dictionary is not set")
        
        sorted_items = sorted(self.incentive_tickers_dict.items(),
                         key=lambda item: (
                            item[1].get('spread', 0),
                            item[1].get('max_loss_dollars', 0),
                            item[1].get('volume', 0)))
        
        self.trade_incentive_dict = {}
        for key, value in sorted_items[:trade_ticker_size]:
            self.trade_incentive_dict[key] = value

    def get_trade_ticker(self):
        if not self.trade_incentive_dict:
            raise ValueError("Trade incentive dictionary is not set")
        
        ticker_list = []
        for ticker in self.trade_incentive_dict.keys():
            ticker_list.append(ticker)
        return ticker_list

    def update_trade_incentive(self, open_incentive_dict: dict, ticker_dict: dict):
        if not self.trade_incentive_dict:
            raise ValueError("Trade incentive dictionary is not set")
        
        tmp_open_incentive_dict = {}
        for incentive in open_incentive_dict:
            if incentive['market_ticker'] in self.trade_incentive_dict:
                end_date = self._parse_iso_datetime(incentive['end_date'])
                # Convert to naive datetime for comparison if timezone-aware
                end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
                if incentive['paid_out'] == 'true' or end_date_naive >= datetime.now():
                    self.trade_incentive_dict.pop([incentive['market_ticker']])
                else:
                    self.trade_incentive_dict[incentive['market_ticker']]['yes_ask_dollars'] = ticker_dict['yes_ask_dollars']
                    self.trade_incentive_dict[incentive['market_ticker']]['yes_bid_dollars'] = ticker_dict['yes_bid_dollars']
                    self.trade_incentive_dict[incentive['market_ticker']]['no_ask_dollars'] = ticker_dict['no_ask_dollars']
                    self.trade_incentive_dict[incentive['market_ticker']]['no_bid_dollars'] = ticker_dict['no_bid_dollars']
                    self.trade_incentive_dict[incentive['market_ticker']]['volume'] = ticker_dict['volume']
            else:
                tmp_open_incentive_dict[incentive['market_ticker']] = incentive
        
        for ticker in self.trade_incentive_dict:
            if ticker not in tmp_open_incentive_dict:
                self.trade_incentive_dict.pop([ticker])

    def get_trade_incentive_dict(self):
        return self.trade_incentive_dict

    def update_trade_incentive_dict(self, ticker_dict: dict):
        if not self.trade_incentive_dict:
            return
        
        for ticker in self.trade_incentive_dict:
            if ticker in self.open_incentive_dict:
                if self.open_incentive_dict[ticker]['paid_out'] == False and self.open_incentive_dict[ticker]['end_date'] > datetime.now():
                    yes_ask_dollars = float(ticker_dict[ticker ]['yes_ask_dollars'])
                    no_ask_dollars = float(ticker_dict[ticker]['no_ask_dollars'])
                    notional_value_dollars = float(ticker_dict[ticker]['notional_value_dollars'])
                    volume = float(ticker_dict[ticker]['volume'])
                    spread = abs(yes_ask_dollars - no_ask_dollars)
                    max_loss_dollars = (yes_ask_dollars + no_ask_dollars - notional_value_dollars) * float(self.open_incentive_dict[ticker]['target_size']) / 2.0
                    self.trade_incentive_dict[ticker]['yes_ask_dollars'] = yes_ask_dollars
                    self.trade_incentive_dict[ticker]['no_ask_dollars'] = no_ask_dollars
                    self.trade_incentive_dict[ticker]['volume'] = volume
                    self.trade_incentive_dict[ticker]['spread'] = spread
                    self.trade_incentive_dict[ticker]['max_loss_dollars'] = max_loss_dollars
                else:
                    self.trade_incentive_dict.pop(ticker)
        return self.trade_incentive_dict