from datetime import datetime, timedelta
import time

class TRADE:

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TRADE, cls).__new__(cls)
            cls.__instance.trade_dict = {}
        return cls.__instance

    @property
    def trade_size(self):
        return self.__trade_size
    
    @trade_size.setter
    def trade_size(self, value: int):
        self.__trade_size = value
    
    @property
    def trade_delta(self):
        return self.__trade_delta
    
    @property
    def expiration_ts(self):
        return self.__expiration_ts
    
    @expiration_ts.setter
    def expiration_ts(self, value: int):
        self.__expiration_ts = value

    @trade_delta.setter
    def trade_delta(self, value: float):
        self.__trade_delta = value

    @property
    def incentive_size(self):
        return self.__incentive_size
    
    @incentive_size.setter
    def incentive_size(self, value: int):
        self.__incentive_size = value

    def get_balance(self, balance: int):
        self.balance = balance
    
    def get_open_positions(self, open_positions: list):
        self.open_positions = open_positions

    def _reverse_cum(self,yes_dollars: list):
        reverse_cum = []
        current_sum = 0
        for price, qty in reversed(yes_dollars):
            current_sum += qty
            reverse_cum.append([price, current_sum])
        return reverse_cum

    def _find_the_last_price_and_qty(self, reverse_cum: list, price_limit: float):
        for price, qty in reverse_cum:
            if float(price) <= float(price_limit):
                return qty
        return self.__incentive_size + 1

    def create_open_order(self,
            ticker: str, 
            order_book: dict,
            order_market_book: dict,
            directoin: str
        ):
        if self.balance <= 0:
            raise ValueError("Insufficient balance")
            return

        order_direction_name = ''
        order_direction = ''
        price_name = ''
        side_name = ''

        # direction is yes or no
        if directoin == 'yes':
            order_direction_name = 'yes_ask_dollars'
            order_direction = 'yes_dollars'
            price_name = 'yes_price_dollars'
            side_name = 'yes'
        else:
            order_direction_name = 'no_ask_dollars'
            order_direction = 'no_dollars'
            price_name = 'no_price_dollars'
            side_name = 'no'

        if self.trade_size * (float(order_book[order_direction_name]) + float(order_book[order_direction_name])) > self.balance:
            # raise ValueError("Insufficient balance")
            pass
        
        reverse_cum = self._reverse_cum(order_market_book[order_direction])
        
        # API expects expiration_ts in seconds (not milliseconds)
        expiration_ts = int((datetime.now() + timedelta(minutes=self.expiration_ts)).timestamp())
        order = {}
        if self._find_the_last_price_and_qty(reverse_cum, float(reverse_cum[0][0]) - float(self.trade_delta)) <= float(self.__incentive_size):
            no_price = float(reverse_cum[0][0]) - float(self.trade_delta)  
            no_cost = no_price * float(self.trade_size)
            if no_cost > float(self.balance):
                raise ValueError("Insufficient NO balance")
            else:
                # no incentive for the no bid price
                # API expects no_price_dollars as a string with 4 decimal places
                # When expiration_ts is provided, time_in_force should be omitted
                order['ticker'] = ticker
                order['side'] = side_name
                order['action'] = "buy"
                order['count'] = self.trade_size
                order['type'] = "limit"
                order[price_name] = f"{no_price:.4f}"
                order['expiration_ts'] = expiration_ts
        
        return order

