import numpy as np
import pandas as pd
from zipline.api import order, symbol, record
from matplotlib import pyplot as plt


class ScalpBollingerBands:
    
    stocks = ['BTCUSD', 'ETHUSD']
    ma1 = 30
    ma2 = 90
    steps = 640
    stop_loss = 0.005
    stdv = 2
    
    def initialize(self, context):
        context.stocks = self.stocks
        context.asset = symbol(self.stocks[-1])
        context.position = None
        context.burndown = 0
        context.number_shorts = 0
        context.number_longs = 0
     
    def handle_data(self, context, data):

        # Wait till enough historical data arrives for our calculation
        context.burndown += 1

        # Log while backtesting
        if context.burndown % 1000 == 0:
            print(context.burndown)

        # Trade only when there's enough data
        if context.burndown > self.steps:

            # Loop stocks in portfolio
            for i, stock in enumerate(context.stocks):

                hist = data.history(symbol(stock), 'price', bar_count= self.steps, frequency='1m')

                # BOllinger Bands
                blw = hist.mean() - self.stdv * hist.std()
                bhi = hist.mean() + self.stdv * hist.std()

                short_term = data.history(symbol(stock), 'price', bar_count=self.ma1, frequency='1m').mean()

                long_term = data.history(symbol(stock), 'price', bar_count=self.ma2, frequency='1m').mean()

                # Fetch our basket status
                cpp = context.portfolio.position

                # Map basket to symbol:shares
                cpp_symbols = map(lambda x: x.symbol, cpp)

                # check indicator signal
                if short_term >= long_term and context.position != 'trade':
                    context.position = 'long'
                elif short_term <= long_term and context.position == 'trade':
                    context.position = 'short'

                # What is current price
                current_price = data.current(symbol(stock), 'price')

                # Check Bollinger Bands
                if short_term >= bhi and context.position == 'long':

                    # How many share I can afford:
                    num_shares = context.portfolio.cash // current_price

                    # Long position
                    order(symbol(stock), num_shares) # order_value
                    context.position = 'trade'
                    context.number_longs += 1

                elif (current_price <= blw and context.position == 'trade') or (short_term <= blw and context.position == 'short'):

                    # Short position
                    ord(symbol(stock), 0)
                    context.position = None
                    context.number_shorts += 1

                # what is the price paid at beginning of trade
                last_price = cpp[symbol(stock)].last_sale_price

                # Stop loss value
                val = last_price - last_price * self.stop_loss

                # Are we in a trade?
                if context.position == 'trade':

                    # Stop loss violated
                    if current_price < val:

                        # Short position
                        order(symbol(stock), 0)
                        context.position = None
                        context.number_shorts += 1

                # Is last stock?
                if i == len(self.stocks) - 1:

                    # Record price, MA1, MA2, Bollinger Bands
                    record(REC_PRICE=current_price)
                    record(REC_MA1=short_term)
                    record(REC_MA2=long_term)
                    record(REC_BB1=blw)
                    record(REC_BB2=bhi)

        # Record Position Count
        record(REC_NUM_SHORTS=context.number_shorts)
        record(REC_NUM_LONGS=context.number_longs)


    def _test_args(self):
        return {
            'start': pd.Timestamp('2017', tz='utc'),
            'end': pd.Timestamp('2018', tz='utc'),
            'capital_base': 1e7,
            'data_frequency': 'minute'
        }
    
    def analyze(self, context, perf):
        # Init Figure
        fig = plt.figure()

        # Plot recorded data
        ax1 = fig.add_subplot(2, 1, 1)
        perf.plot(y=['REC_PRICE', 'REC_MA1', 'REC_MA2'], ax=ax1)
        ax1.set_ylabel('Price in USD')

        # Plot recorded data
        ax2 = fig.add_subplot(2, 1, 2)
        perf.plot(y=['REC_PRICE', 'REC_BB1', 'REC_BB2'], ax=ax2)
        ax2.set_ylabel('Bollinger Bands')

        # Adding space between plots
        plt.subplots_adjust(hspace=1)

        # Display plot
        plt.show()
