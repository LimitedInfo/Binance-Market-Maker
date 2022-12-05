import ccxt
import re
import time
import datetime
import pandas as pd
import numpy as np
from ccxt import OrderNotFound

import crypto_trader_functions as ctf

current_milli_time = lambda: int(round(time.time() * 1000))

max_perc_dec_trade = .002
min_spread = .003
max_perc_dec_timeframe = '3m'
trading_pair = 'STRAT/ETH'

coin_min_bids = ctf.coin_min(trading_pair, multiplier=.2)


# print(ctf.open_orders(trading_pair))
# print(ctf.id_open_order(trading_pair))
# print(ctf.id_sell_order(trading_pair))
# print()

checker = 0


def market_buyer(checker):
    checker += 1
    if checker == 1 or checker % 5 == 0:
        if ctf.hows_the_market_doing(trading_pair, price_dec_perc=max_perc_dec_trade) == 'good':
            print("market is good")
            if ctf.true_spread(trading_pair, coin_min=coin_min_bids) > min_spread:
                print(f"true spread greater than {min_spread}")
                if ctf.free_balance(trading_pair)['Quote'] >= .01:
                    print("balance is sufficient")
                    print("making order")
                    true_bid = ctf.true_bid(trading_pair, coin_min=coin_min_bids) * 1.0005
                    ctf.exchange.create_order(symbol=trading_pair, type='limit', side='buy',
                                              amount=(ctf.free_balance(trading_pair)['Quote'] * .999) / true_bid,
                                              price=true_bid)
                else:
                    print("balance insufficient sleeping 5 seconds")
                    time.sleep(5)
            else:
                print("spread not good, sleeping")
                time.sleep(5)
        else:
            print("market not good sleeping 90 seconds")
            time.sleep(90)
    else:
        if ctf.free_balance(trading_pair)['Quote'] >= .01:
            print("balance is sufficient")
            print("making order")
            true_bid = ctf.true_bid(trading_pair, coin_min=coin_min_bids) * 1.0005
            ctf.exchange.create_order(symbol=trading_pair, type='limit', side='buy',
                                      amount=(ctf.free_balance(trading_pair)['Quote'] * .999) / true_bid,
                                      price=true_bid)
        else:
            print("balance insufficient sleeping 5 seconds")
            time.sleep(5)


    if not ctf.id_open_order(trading_pair):
        print("no open orders, running from start")
        market_buyer(checker)
    while ctf.am_i_the_bid_leader(trading_pair, coin_min_bids) is True:
        print("currently the bid leader, waiting")
        time.sleep(.25)

    try:
        ctf.exchange.cancel_order(ctf.id_open_order(trading_pair), symbol=trading_pair)
    except TypeError:
        print("No open orders, running again.")
        market_buyer(checker)
    except OrderNotFound:
        print("order not found, running again")
        market_buyer(checker)
    print("order successfully canceled, running again")
    market_buyer(checker)

market_buyer(checker)