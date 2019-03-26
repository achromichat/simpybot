import ccxt
import numpy
import talib
from talib import *
import time
import json
import datetime
import keys

# TESTING GITHUB

# Use current position data in trade decision

# build in the logic to track price movements over time - not just increase, but several increases / trend metric

# Upload to github - ensure key importing is safe and works first! 

# Connect and verify OpenVPN connection to CH on Raspberry Pi

# Rewrite this in Go?

exch = ccxt.bitmex({
    'apiKey': keys.exchange[0],
    'secret': keys.exchange[1],
    'enableRateLimit':True,})
exch.load_markets()

# PARAMETERS
symbol = 'BTC/USD'
currency = 'BTC'
# timer variable (starts at 5 min)
frame = '1m' # can be 1m, 1h, 1d, 1M, 1y
frame_secs = 5 #60 # compute the frame's duration in seconds (for loop)
time_multiplier = 60000 # 1m = 60000, 1h = 3600000, 1d = 86400000
short_period = 20
long_period = 50

# ALL TIME P/L
# will require i/o from a log file? 

# INIT PRICEs
last_price = exch.fetch_order_book('BTC/USD', 1)['bids'][0][0] # safeguard: if len (orderbook['bids']) > 0 else None
current_price = 0

# INIT Indicators
sma_bullish = True
price_increase = True
high_avail_funds = True
sma_short_last = 0
sma_long_last = 0
## Positions

# INIT Balances and Positions
starting_balance = exch.fetch_balance()[currency]['total']
current_balance = starting_balance
last_trade_balance = 0
free_balance = 0
used_balance = 0
open_positions = []

# INIT Order Size
order_size = 0

# Print live P&L when trades get executed
def trade_debug():
    global new_balance
    global currency
    global last_trade_balance
    global starting_balance
    # print current acct value (value of all closed positions + open positions)
    new_balance = exch.fetch_balance()[currency]['total']
    print("LIVE P/L")
    print("    New Balance: ", new_balance)
    # print delta between current acct value and last acct value
    if last_trade_balance != 0:
        last_trade_delta = ((new_balance - last_trade_balance) / last_trade_balance) * 100
        print("    Delta since last trade: ", last_trade_delta, "%")
    overall_delta = ((new_balance - starting_balance) / starting_balance) * 100
    print("    Overall Delta: ", overall_delta, "%")

def sma_debug():
    global sma_bullish
    global sma_short_last
    global sma_long_last
    if (sma_bullish):
        print ("sma BULLish")
    else:
        print ("sma BEARish")
    print ("    Short", sma_short_last)
    print ("    Long", sma_long_last)

def balances_debug():
    global free_balance
    global used_balance
    global open_positions
    print("Free: ", free_balance, "\n Used: ", used_balance, "\n Open Position (contracts, markPrice):", open_positions)

def price_movement_debug():
    global current_price
    global last_price
    print("Current price: ", current_price)
    print("    Up: ", current_price - last_price)

def all_debugs():
    trade_debug()
    sma_debug()
    balances_debug()
    price_movement_debug()

def sma_calculator():
    global sma_short_last
    global sma_long_last
    global sma_bullish
    global time_multiplier
    global long_period
    global short_period
    global symbol
    global frame
    
    candles_time = exch.milliseconds () - (time_multiplier * (long_period - 1)) # pull long_period of candles
    candles = exch.fetch_ohlcv(symbol, frame, candles_time) # pull candles back 2x the long period
### Need to 2x the candles_time? Check if the SMAs change values with diff candle lookbacks
    opens = []
    for candle in candles:
        opens.append(candle[1]) # index 1 is the Open price
    opens_array = numpy.asarray(opens) # convert to numpy_array for TA lib

    sma_short = talib.SMA(opens_array, timeperiod=short_period)
    sma_short_last = sma_short[long_period - 1]

    sma_long = talib.SMA(opens_array, timeperiod=long_period)
    sma_long_last = sma_long[long_period - 1]

    # Set SMA Indicator Value
    sma_bullish = sma_short_last > sma_long_last

def balance_fetch():
    global current_balance
    global free_balance
    global used_balance
    global last_trade_balance # Only set when a trade is made
    global open_positions
    global symbol
    global high_avail_funds
    
    balances = exch.fetch_balance()
    current_balance = balances[currency]['total']
    free_balance = balances[currency]['free'] # Currently available for trading (for BitMEX)
    used_balance = balances[currency]['used'] # Currently held in a position (for BitMEX)
    open_positions_raw = exch.private_get_position({
        'filter': json.dumps({ # .dumps gets a readable format
            "isOpen": True,
            "symbol": "XBTUSD" # using XBT for this implicit method
        }),
        'columns': 'currentQty,unrealisedPnl,liquidationPrice,markPrice'
    })
    open_positions = open_positions_raw[0]['currentQty'], open_positions_raw[0]['markPrice']
    # Available Funds Indicator
    high_avail_funds = free_balance > (.25 * current_balance)

def position_is_long():
    if open_positions_raw[0]['currentQty']
        return True
    else:
        return False

def price_fetch():
    global current_price
    global symbol
    global price_increase
    global last_price

    current_price = exch.fetch_order_book(symbol, 1)['bids'][0][0] # safeguard: if len (orderbook['bids']) > 0 else None
    # Price Increase Indicator
    price_increase = last_price <= current_price

def order_size_calculation():
    global order_size
    # place orders with 10% of free capital, in Base currency (USD), rounded to nearest integer (contracts)
    order_size = round(free_balance * .1 * current_price)
    order_size = 1 ## FOR TESTING PURPOSES

# Trading loop
while True:

    ## USE THIS TO CATCH ERRORS
    ## try:
    ## except:
        ## print('an error occured')
        ## time.sleep('5')

    ## Check that --- exch.has['fetchOHLCV'] and exch.has['createMarketOrder']:
    print("")
    print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    
    sma_calculator() # and SMA cross indicator set
    balance_fetch() # and available funds indicator set
    price_fetch() # and price increase indicator set

    order_size_calculation() # calculate order size

    all_debugs() # print values

    # Bullish Price Trend 
    if sma_bullish and price_increase:
        print ("BULLISH TO THE MOON")
        if high_avail_funds or !position_is_long(): ## lots of avail cash or net short position!
            last_trade_balance = current_balance # order is being placed, so save balance for P/L
            print ("    High funds available. Buy order of ", order_size, " contracts.")
            buy_order = exch.create_market_buy_order (symbol, order_size)
            # place limit buy order at $0.5 below market? To get rebates... but very complex then if doesn't execute!
            
            # Catch insufficient funds errors! Not necessary if orders placed based on free capital
            
            # Set stops and take profits
            print("    set a sell stop X percent down")
            print("    set a take profit order")

            trade_debug()

    #   The above will slowly add to the trend (long) as that trend reaffirms with moving avg and price increases
   
    # Bearish Price Trend
    elif not sma_bullish and not price_increase:
        print ("BEARISH PULLDOWN")
        if high_avail_funds or position_is_long(): ## lots of avail cash or net long position!
            last_trade_balance = current_balance # order is being placed, so save balance for P/L
            print ("    High funds available. Sell order of ", order_size, " contracts.")
            sell_order = exch.create_market_sell_order (symbol, order_size) # place market sell order with 10% of free capital?
                # Are Sell orders just NEGATIVE amount buy orders? 

            # Catch insufficient funds errors! Not necessary if orders placed based on free capital
            
            # Set stops and take profits
            print("    set a buy stop X percent up")
            print("    set a take profit order lower down")

            trade_debug()

        #   The above will slowly add to the trend (short) as that trend reaffirms with moving avg and price decreases
    else:
        print ("no action, weak trend")

    last_price = current_price

    time.sleep(frame_secs)

# HAVE A Way to print P/L of trades when closed out. Would help me compute how successful the bot is. 
# Also compute an over-time P/L as well as win/loss rate. Remember, winners need to win big, losers small. 
# Testing trade printing
# trades = exch.fetchTrades ('BTC/USD', exch.parse8601 ('2018-12-26T02:27:00Z'), 1)
# print(trades)