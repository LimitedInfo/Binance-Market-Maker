import ccxt
import re
import time
import numpy as np
import config

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    divisor = pow(10, n)
    dec_round_f = f * divisor
    return int(dec_round_f) / divisor


exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': config.api_key,
    'secret': config.api_secret,
    'timeout': 30000,
    'enableRateLimit': True,
})
binance_markets = exchange.load_markets()

_since = 1588977738757 + 86400000
#
# print(exchange.markets['BTC/USDT'])
# trading_pair = 'SNT/ETH'
# print(exchange.markets[trading_pair])

# def market_maker_order(tra):

# print(exchange.fetch_ticker(trading_pair))

# if spread is higher than .005% then:
# check for highest bid price. place order .0005% above highest bid price (8 decimal places).
# increase or decrease this buying price depending on the size of the spread.

# if spread is too low, check orders until .03 eth is traded. then check spread if spread is above .005%:
# place order .0001% above the next buy order.

# once order is done. check for lowest ask price.
# if ask price is .002% or less above purchase price for > x eth. and the trade history is .002% or less above purchase.
# keep putting in sell orders for ask + bid / 2
# else: check for lowest ask price. place order .0005% below that price.
# check your order is still lowest if not repeat previous logic

def extract(lst, item_index):
    return [item[item_index] for item in lst]


def order_book(trading_pair, depth=5):
    orderbook = exchange.fetch_l2_order_book(trading_pair, depth)
    return orderbook


def true_spread(trading_pair, depth=10, ask_or_bid='bid', coin_min=1000):
    """
    You can also get the most relevant bid or ask order from here depending on the coin min that is used.
    Coin min is a variable that is set outside this function.

    :param trading_pair:
    :param depth: number of orders that function checks
    :param coin_min: min number of coins to use the price for the spread
    :return: tuple: spread as a percentage, bid price, ask price
    """
    if ask_or_bid == 'bid':
        coin_min = bid_coin_min
    if ask_or_bid == 'ask':
        coin_min = ask_coin_min

    cum_quantity_bid = 0
    cum_quantity_ask = 0
    orderbook = order_book(trading_pair, depth)
    for depth_num in range(depth):
        cum_quantity_bid += orderbook['bids'][depth_num][1]
        if cum_quantity_bid > coin_min:
            index_for_bid = depth_num
            break

    for depth_num in range(depth):
        cum_quantity_ask += orderbook['asks'][depth_num][1]
        if cum_quantity_ask > coin_min:
            index_for_ask = depth_num
            break

    return (orderbook['asks'][index_for_ask][0] / orderbook['bids'][index_for_bid][0]) - 1, \
           orderbook['bids'][index_for_bid][0], orderbook['asks'][index_for_ask][0]


def limits_and_precision(trading_pair):
    """
    :param trading_pair:
    :return: dictionary of min limit for trade then precision amount.
    """
    return {'Min Limit': exchange.markets[trading_pair]['limits']['amount']['min'],
            'Precision': exchange.markets[trading_pair]['precision']['amount']}


def id_open_order(trading_pair):
    """
    :param trading_pair:
    :return: ID for the most recent buy order.
    """
    return exchange.fetch_open_orders(symbol=trading_pair)[0]['id']


def id_sell_order(trading_pair):
    """
    :param trading_pair:
    :return: returns ID for most recent sell order.
    """
    open_orders = exchange.fetch_open_orders(symbol=trading_pair)
    len_open_orders = len(open_orders)
    return open_orders[len_open_orders-1]['id']


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


def am_i_the_bid_leader(trading_pair):
    """
    :param trading_pair:
    :return: Returns true/false depending on if you are above relevant bid orders. Returns true if error occurs.
    """
    try:
        if exchange.fetch_open_orders(symbol=trading_pair)[0]['price'] >= true_spread(trading_pair)[1]:
            return True
        else:
            return False
    except:
        return True


def am_i_the_ask_leader(trading_pair):
    """
    :param trading_pair:
    :return: Returns true/false depending on if you are below relevant ask orders. Returns true if error occurs.
    """
    try:
        open_orders = exchange.fetch_open_orders(symbol=trading_pair)
        len_open_orders = len(open_orders)
        if exchange.fetch_open_orders(symbol=trading_pair)[len_open_orders-1]['price'] <= true_spread(trading_pair, ask_or_bid='ask')[2]:
            return True
        else:
            return False
    except:
        return True


def hows_the_market_doing(trading_pair, price_dec_perc, timeframe='5m', limit=5):
    """
    :param trading_pair:
    :param price_dec_perc: decimal that will be subtracted from one and multiplied to the 2 most recent periods closing price.
    :param timeframe: timeframe for the closing prices
    :param limit: number of closing prices considered.
    :return: 'good' or 'bad'
    """
    ohlcv = exchange.fetch_ohlcv(trading_pair, timeframe=timeframe, limit=limit)

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
        relevant_bid_ask = true_spread(trading_pair, ask_or_bid='other', coin_min=1000)[1]
        return (current_order_price(trading_pair) / relevant_bid_ask) - 1

    if bid_or_ask == 'ask':
        relevant_bid_ask = true_spread(trading_pair, ask_or_bid='other', coin_min=1000)[2]
        return (relevant_bid_ask / current_order_price(trading_pair)) - 1







def market_maker(trading_pair):
    try:
        print("in market maker")
        # if len(exchange.fetch_open_orders(symbol=trading_pair)) == 0:
        if exchange.fetch_closed_orders(symbol=trading_pair, since=_since)[-1]['side'] == 'sell':
            print("last order sell")
            spread_bid_ask = true_spread(trading_pair)
            if spread_bid_ask[0] > spread and hows_the_market_doing(trading_pair, price_dec_perc=.004 == 'good'):
                print("greater than .006")

                exchange.create_order(symbol=trading_pair, type='limit', side='buy',
                                      amount=free_balance(trading_pair)['Quote'] / spread_bid_ask[1] * percent_to_buy,
                                      price=spread_bid_ask[1] * 1.0005)

                time.sleep(1)

                while exchange.fetch_closed_orders(symbol=trading_pair, since=_since)[-1]['side'] == 'sell':
                    if am_i_the_bid_leader(trading_pair) is False or true_spread(trading_pair)[0] < 0.0055:
                        print("not the bid leader")
                        exchange.cancel_order(id_open_order(trading_pair), symbol=trading_pair)
                        market_maker(trading_pair)
                    # time.sleep(10)

                return 1

            else:
                print("spread insufficient or price is decreasing.")
                while true_spread(trading_pair)[0] < spread:
                    if len(exchange.fetch_open_orders(symbol=trading_pair)) > 0:
                        time.sleep(3)
                        continue
                    else:
                        not_leader_trade_price = true_spread(trading_pair)[2] * .993
                        exchange.create_order(symbol=trading_pair, type='limit', side='buy',
                                              amount=free_balance(trading_pair)['Quote'] / not_leader_trade_price * percent_to_buy,
                                              price=not_leader_trade_price)

                exchange.cancel_order(id_open_order(trading_pair), symbol=trading_pair)
                market_maker(trading_pair)

        else:
            return 1
    except ccxt.NetworkError as e:
        print(exchange.id, 'fetch_order_book failed due to a network error:', str(e))
        return 1
    except ccxt.ExchangeError as e:
        print(exchange.id, 'fetch_order_book failed due to exchange error:', str(e))
        return 1
    except Exception as e:
        print(exchange.id, 'fetch_order_book failed with:', str(e))
        return 1
# TODO: change cycle of buy -> sell, buy -> sell to just continuously buy and sell at the same time. 

def market_seller(trading_pair, target_selling_price):
    try:
        print("in market seller")
        spread_bid_ask = true_spread(trading_pair, ask_or_bid='ask')
        if exchange.fetch_closed_orders(symbol=trading_pair, since=_since)[-1]['side'] == 'buy':
            # TODO: base emergency selling on actual trade history, not current asking price.
            if spread_bid_ask[2] < target_selling_price * .995:#exchange.fetch_ohlcv(trading_pair, timeframe='3m', limit=2)[-1][4] < target_selling_price * .99:
                print("state of emergency.")
                exchange.create_order(symbol=trading_pair, type='limit', side='sell',
                                      amount=free_balance(trading_pair)['Base'],
                                      price=spread_bid_ask[2] * .999)
                state_of_emergency = 1
            else:
                print("normal target trade.")
                exchange.create_order(symbol=trading_pair, type='limit', side='sell',
                                      amount=free_balance(trading_pair)['Base'],
                                      price=target_selling_price * .9997)
                state_of_emergency = 0

            # TODO: make it so that seller is fine with not being leader, when not below target price.

            while exchange.fetch_closed_orders(symbol=trading_pair, since=_since)[-1]['side'] == 'buy':
                if am_i_the_ask_leader(trading_pair) is False and state_of_emergency == 1:
                    print("cancelling")
                    exchange.cancel_order(id_sell_order(trading_pair), symbol=trading_pair)
                    market_seller(trading_pair, target_selling_price)

                else:
                    print("waiting.")
                    time.sleep(15)
                    if am_i_the_ask_leader(trading_pair) is False or exchange.fetch_open_orders(symbol=trading_pair)[0]['price'] <= true_spread(trading_pair, ask_or_bid='ask')[2] * .996:
                        exchange.cancel_order(id_sell_order(trading_pair), symbol=trading_pair)
                        market_seller(trading_pair, target_selling_price)

            return 1

        else:
            return 1
    except ccxt.NetworkError as e:
        print(exchange.id, 'fetch_order_book failed due to a network error:', str(e))
        return 1
    except ccxt.ExchangeError as e:
        print(exchange.id, 'fetch_order_book failed due to exchange error:', str(e))
        return 1
    except Exception as e:
        print(exchange.id, 'fetch_order_book failed with:', str(e))
        return 1
    # if len(exchange.fetch_open_orders(symbol=trading_pair)) >= 1:
    #     print("> or = to 1")
    #     if am_i_the_ask_leader(trading_pair) is False:
    #         print("cancelling")
    #         exchange.cancel_order(id_sell_order(trading_pair), symbol=trading_pair)
    #
    #     else:
    #         while exchange.fetch_closed_orders(symbol=trading_pair)[-1]['side'] == 'buy':
    #             if true_spread(trading_pair)[2] < exchange.fetch_open_orders(symbol=trading_pair)[0]['price']:
    #                 exchange.cancel_order(id_sell_order(trading_pair), symbol=trading_pair)

                    # market_seller(trading_pair, target_selling_price)

        # market_seller(trading_pair, target_selling_price)


trading_pair = input("trading pair (e.x. SNT/ETH):")
if not trading_pair:
    trading_pair = 'SNT/ETH'

spread = input("desired spread (e.x. .006):")
if not spread:
    spread = .006
if isinstance(spread, str):
    spread = float(spread)
# print(free_balance(trading_pair)['Quote'], order_book(trading_pair)['Orderbook']['bids'][0][0]*.999)
# spread_bid_ask = true_spread(trading_pair)

# print(exchange.fetch_open_orders(symbol=trading_pair))

# print(limits_and_precision(trading_pair))
# print(free_balance(trading_pair)['Base'] * spread_bid_ask[2] * 1.001, free_balance(trading_pair)['Quote'] / spread_bid_ask[1] * .999)

percent_to_buy = float(input("percent of balance to buy (e.x. .5):"))
# epoch = datetime.datetime.utcfromtimestamp(0)
# def unix_time_millis(dt):
#     return (dt - epoch).total_seconds() * 1000.0

# print(unix_time_millis(datetime.datetime.today()))
ohlcv = exchange.fetch_ohlcv(trading_pair, timeframe='3m', limit=5)
# ohlcv1m = exchange.fetch_ohlcv(trading_pair, timeframe='3m', limit=10)

# print(exchange.fetch_closed_orders(symbol=trading_pair, since=1588977738757))

# print(ohlcv1m)
bid_coin_min = np.average(extract(order_book(trading_pair, depth=10)['bids'],1)) * .3
ask_coin_min = np.average(extract(order_book(trading_pair, depth=10)['bids'],1))

target_percent = .006

# TODO: start selling as soon as sufficient base currency is acquired.
# TODO: fix error where not all is sold. new balance is under sufficient for order therefore program freezes
# TODO: try solution where you are more specific about exceptions.
while True:
    while hows_the_market_doing(trading_pair, price_dec_perc=.004) == 'good':
        market_maker(trading_pair)
        market_seller(trading_pair, exchange.fetch_closed_orders(symbol=trading_pair, since=_since)[-1]['price'] * (1 + target_percent))
        closed_orders = exchange.fetch_closed_orders(symbol=trading_pair, since=_since)
        print(closed_orders[-1]['cost'] - closed_orders[-2]['cost'])
        ohlcv = exchange.fetch_ohlcv(trading_pair, timeframe='3m', limit=5)

    print("market is not feeling too well...")
    print("waiting...")
    time.sleep(10)


market_seller(trading_pair, exchange.fetch_closed_orders(symbol=trading_pair, since=_since)[-1]['price'] * (1 + target_percent))






def make_order(symbol_list, percent_purchase):
    foo = re.search("/", symbol_list[2])
    coin_one = symbol_list[2][:foo.start()]

    foo = re.search("/", symbol_list[1])
    coin_two = symbol_list[1][foo.end():]

    foo = re.search("/", symbol_list[0])
    coin_three = symbol_list[0][foo.end():]

    balance = exchange.fetch_balance()[coin_one]['free'] * percent_purchase
    print(balance)
    order = exchange.create_order(symbol_list[2], type='market', side='sell', amount=balance)
    # order2 = exchange.create_market_buy_order(symbol_list[2], amount=amount)

    balance = exchange.fetch_balance()[coin_two]['free']
    print(balance)
    amount = balance / exchange.fetch_order_book(coin_two, limit=1)['asks'][0][0]
    order1 = exchange.create_market_buy_order(symbol_list[1], amount=amount)
    # order1 = exchange.create_order(symbol_list[1], type='market', side='sell', amount=balance)

    balance = exchange.fetch_balance()[coin_three]['free'] * percent_purchase
    print(balance)
    amount = balance / exchange.fetch_order_book(coin_three, limit=1)['asks'][0][0]
    order2 = exchange.create_market_buy_order(symbol_list[0], amount=amount)
    # order = exchange.create_order(symbol_list[0], type='market', side='sell', amount=balance)


