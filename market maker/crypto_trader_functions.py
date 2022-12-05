import ccxt
import re
import numpy as np
import time
import config

exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': config.api_key,
    'secret': config.api_secret,
    'timeout': 30000,
    'enableRateLimit': False,
})
# binance_markets = exchange.load_markets()
#
_since = int(round(time.time() * 1000)) - 1200000


def extract(lst, item_index):
    return [item[item_index] for item in lst]


def order_book(trading_pair, depth=5):
    orderbook = exchange.fetch_l2_order_book(trading_pair, depth)
    return orderbook


def true_spread(trading_pair, coin_min, depth=10):
    """
    You can also get the most relevant bid or ask order from here depending on the coin min that is used.
    Coin min is a variable that is set outside this function.

    :param trading_pair:
    :param depth: number of orders that function checks
    :param coin_min: min number of coins to use the price for the spread
    :return: tuple: spread as a percentage, bid price, ask price
    """

    return (true_ask(trading_pair, coin_min, depth) / true_bid(trading_pair, coin_min, depth)) - 1


def coin_min(trading_pair, depth=10, multiplier=1, bids_asks='bids'):
    return np.average(extract(order_book(trading_pair, depth=depth)[bids_asks], 1)) * multiplier


def true_bid(trading_pair, coin_min, depth=10):
    # print(coin_min)
    cum_quantity_bid = 0

    orderbook = order_book(trading_pair, depth)
    for depth_num in range(depth):
        cum_quantity_bid += orderbook['bids'][depth_num][1]
        if cum_quantity_bid > coin_min:
            index_for_bid = depth_num
            break
    try:
        return orderbook['bids'][index_for_bid][0]
    except:
        print('using 11th index true bid')
        return orderbook['bids'][depth-1][0]


def true_ask(trading_pair, coin_min, depth=10):
    # print(coin_min)
    cum_quantity_ask = 0

    orderbook = order_book(trading_pair, depth)
    for depth_num in range(depth):
        cum_quantity_ask += orderbook['asks'][depth_num][1]
        if cum_quantity_ask > coin_min:
            index_for_ask = depth_num
            break
    try:
        return orderbook['asks'][index_for_ask][0]
    except:
        print('using 11th index true ask')
        return orderbook['asks'][depth-1][0]


def limits_and_precision(trading_pair):
    """
    :param trading_pair:
    :return: dictionary of min limit for trade then precision amount.
    """
    return {'Min Limit': exchange.markets[trading_pair]['limits']['amount']['min'],
            'Precision': exchange.markets[trading_pair]['precision']['amount']}


def open_orders(trading_pair, since=_since):
    return exchange.fetch_open_orders(symbol=trading_pair, since=since)


def id_open_order(trading_pair):
    """
    :param trading_pair:
    :return: ID for the most recent buy order.
    """
    open_orders = exchange.fetch_open_orders(symbol=trading_pair, since=_since)
    for order in open_orders:
        if order['side'] == 'buy':
            id = order['id']
            return id
    return None



def id_sell_order(trading_pair):
    """
    :param trading_pair:
    :return: returns ID for most recent sell order.
    """
    open_orders = exchange.fetch_open_orders(symbol=trading_pair, since=_since)
    for order in open_orders:
        if order['side'] == 'sell':
            id = order['id']
            return id
    return None


def most_recent_sell_trade(trading_pair):
    trades = exchange.fetch_my_trades(trading_pair, limit=30)
    for trade in reversed(trades):
        if trade['side'] == 'buy':
            last_buy = trade['price']
            break
    return last_buy


def target_sell_price(trading_pair, desired_spread):
    trades = exchange.fetch_trades(trading_pair, since=_since)
    for trade in reversed(trades):
        if trade['side'] == 'buy':
            last_buy = trade['price']
            break
    return last_buy * (1 + desired_spread)


def free_balance(trading_pair):
    """
    :param trading_pair:
    :return: dictionary of free balance for base currency then quote currency
    """
    index = re.search("/", trading_pair)
    base = trading_pair[:index.start()]
    quote = trading_pair[index.end():]

    return {'Base': exchange.fetch_balance()[base]['free'],
            'Quote': exchange.fetch_balance()[quote]['free']}


def am_i_the_bid_leader(trading_pair, coin_min_bid):
    """
    :param coin_min_bid:
    :param trading_pair:
    :return: Returns true/false depending on if you are above relevant bid orders. Returns true if error occurs.
    """
    try:
        if exchange.fetch_order(id_open_order(trading_pair), symbol=trading_pair)['price'] >= true_bid(trading_pair, coin_min_bid):
            return True
        else:
            return False
    except:
        return False


def am_i_the_ask_leader(trading_pair, coin_min_ask):
    """
    :param coin_min_ask:
    :param trading_pair:
    :return: Returns true/false depending on if you are below relevant ask orders. Returns true if error occurs.
    """
    #
    # open_orders = exchange.fetch_open_orders(symbol=trading_pair)
    # len_open_orders = len(open_orders)
    try:
        if exchange.fetch_order(id_sell_order(trading_pair), symbol=trading_pair)['price'] <= true_ask(trading_pair, coin_min_ask):
            return True
        else:
            return False
    except IndexError:
        print("am i the ask leader index error")
        return False
    except TypeError:
        print("am i the ask leader type error")
        return False


def keep_trading(trading_pair, function, buy_sell_func):
    try:
        function
    except IndexError:
        if free_balance(trading_pair)['Quote'] / true_bid(trading_pair) > amount_to_buy:
            buy_sell_func




def hows_the_market_doing(trading_pair, price_dec_perc, timeframe='3m', limit=5):
    """
    :param trading_pair:
    :param price_dec_perc: decimal that will be subtracted from one and multiplied to the 2 most recent periods closing price.
    :param timeframe: timeframe for the closing prices
    :param limit: number of closing prices considered.
    :return: 'good' or 'bad'
    """
    ohlcv = exchange.fetch_ohlcv(trading_pair, timeframe=timeframe, limit=limit)
    # TODO: use most recent candle ehre
    if ohlcv[-1][4] > ohlcv[-2][4] * (1 - price_dec_perc):
        return 'good'
    else:
        return 'bad'


def current_order_price(trading_pair):
    return exchange.fetch_open_orders(symbol=trading_pair)[0]['price']


def any_open_orders_buyside(trading_pair):
    open_orders = exchange.fetch_open_orders(symbol=trading_pair, since=_since)
    for open_order in open_orders:
        if open_order['side'] == 'buy':
            return True
    return False


def any_open_orders_sellside(trading_pair):
    open_orders = exchange.fetch_open_orders(symbol=trading_pair, since=_since)
    for open_order in open_orders:
        if open_order['side'] == 'sell':
            return True
    return False


def current_order_vs_spread(trading_pair, bid_or_ask: str):
    """
    not sure why you would want to compare your current asking price to relevant bidding price but it is possible here.

    :param trading_pair:
    :param bid_or_ask: str of 'bid' or 'ask' to determine which relevant price you are looking for.
    :return: spread between relevant bid/ask price and your current order price.
    """

    if bid_or_ask == 'bid':
        relevant_bid_ask = true_bid(trading_pair)
        return (current_order_price(trading_pair) / relevant_bid_ask) - 1

    if bid_or_ask == 'ask':
        relevant_bid_ask = true_ask(trading_pair)
        return (relevant_bid_ask / current_order_price(trading_pair)) - 1