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

    @property
    def trade_price_limit(self):
        return self.__trade_price_limit
    
    @trade_price_limit.setter
    def trade_price_limit(self, value: float):
        self.__trade_price_limit = value

    @property
    def stop_trade_time(self):
        return self.__stop_trade_time
    
    @stop_trade_time.setter
    def stop_trade_time(self, value: int):
        self.__stop_trade_time = value

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
        self.trade_incentive_dict = {}

        try:
            for incentive in self.open_incentive_dict:
                if incentive['market_ticker'] in ticker_dict:
                    end_date = self._parse_iso_datetime(incentive['end_date'])
                    # Convert to naive datetime for comparison if timezone-aware
                    end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
                    # Allow 5 minutes leeway for the timestamp comparison
                    curr_date_time = datetime.now() - timedelta(seconds=self.__stop_trade_time)
                    if incentive['paid_out'] == False and end_date_naive > curr_date_time and incentive['incentive_type'] == 'liquidity':
                        curr_ticker = incentive['market_ticker']
                        # if abs(float(ticker_dict[curr_ticker]['yes_ask_dollars'])) <= self.__trade_price_limit or abs(float(ticker_dict[curr_ticker]['no_ask_dollars'])) <= self.__trade_price_limit:
                        #     continue
                        # else:
                        if incentive['target_size'] is None or ticker_dict[curr_ticker]['yes_ask_dollars'] is None or ticker_dict[curr_ticker]['no_ask_dollars'] is None or ticker_dict[curr_ticker]['volume'] is None:
                            continue
                        else:
                            # yes_book = self._reverse_cum(ticker_dict[curr_ticker]['yes_ask_dollars'])
                            # no_book = self._reverse_cum(ticker_dict[curr_ticker]['no_ask_dollars'])
                            # yes_idx = self._find_the_last_price_and_qty(yes_book, incentive['target_size'])
                            # no_idx = self._find_the_last_price_and_qty(no_book, incentive['target_size'])
                            # yes_price = float(yes_book[yes_idx][0])
                            # no_price = float(no_book[no_idx][0])
                            # if yes_price > self.__trade_price_limit and no_price > self.__trade_price_limit:
                            #     continue

                            yes_ask_dollars = float(ticker_dict[curr_ticker]['yes_ask_dollars'])
                            no_ask_dollars = float(ticker_dict[curr_ticker]['no_ask_dollars'])
                            volume = float(ticker_dict[curr_ticker]['volume'])
                            spread = abs(yes_ask_dollars - no_ask_dollars)
                            # max_loss_dollars = (yes_ask_dollars + no_ask_dollars - notional_value_dollars) * float(incentive['target_size'])
                            tmp_dict = {
                                'ticker': curr_ticker,
                                'start_date': incentive['start_date'],
                                'discount_factor_bps': incentive['discount_factor_bps'],
                                'end_date': incentive['end_date'],
                                'id': incentive['id'],
                                'title': ticker_dict[curr_ticker]['title'],
                                'rules_primary': ticker_dict[curr_ticker]['rules_primary'],
                                'incentive_type': incentive['incentive_type'],
                                'paid_out': incentive['paid_out'],
                                'period_reward': incentive['period_reward'],
                                'target_size': incentive['target_size'],
                                'yes_ask_dollars': yes_ask_dollars,
                                'no_ask_dollars': no_ask_dollars,
                                'volume': volume,
                                'spread': spread,
                                # 'max_loss_dollars': max_loss_dollars
                            }
                            self.trade_incentive_dict[incentive['market_ticker']] = tmp_dict
        except Exception as e:
            print(f"Error get_incentive_tickers tickers on the [INCENTIVE_PROGRAM]: {e}")
        finally:
            pass

    def get_trade_ticker(self):
        if not self.trade_incentive_dict:
            raise ValueError("Trade incentive dictionary is not set")
        
        ticker_list = []
        for ticker in self.trade_incentive_dict.keys():
            ticker_list.append(ticker)
        return ticker_list

    def get_trade_incentive_dict(self):
        return self.trade_incentive_dict
