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
coins_to_buy = 3
coin_min_bids = ctf.coin_min(trading_pair, multiplier=.2)
coin_min_ask = ctf.coin_min(trading_pair, bids_asks='asks', multiplier=.5)

def market_seller():
    target_selling_price = ctf.target_sell_price(trading_pair, desired_spread=min_spread + .0005)
    emergency_mode = False
    if ctf.free_balance(trading_pair)['Base'] * (ctf.true_ask(trading_pair, coin_min=coin_min_ask) * .999) > .01:
        if ctf.true_ask(trading_pair, coin_min=coin_min_ask) < ctf.most_recent_sell_trade(trading_pair):
            print("emergency mode.")
            emergency_mode = True
            ctf.exchange.create_order(symbol=trading_pair, type='limit', side='sell',
                                      amount=ctf.free_balance(trading_pair)['Base'],
                                      price=ctf.true_ask(trading_pair, coin_min=coin_min_ask) * .999)
        else:
            print("normal target trade.")
            emergency_mode = False
            ctf.exchange.create_order(symbol=trading_pair, type='limit', side='sell',
                                      amount=ctf.free_balance(trading_pair)['Base'],
                                      price=ctf.most_recent_sell_trade(trading_pair) * (1+min_spread))
    else:
        print("insufficient balance")
        time.sleep(5)

    if not ctf.id_sell_order(trading_pair):
        market_seller()

    # TODO: make seller check to see if any remaining balance is waiting to be sold.
    if not emergency_mode:
        while ctf.true_ask(trading_pair, coin_min=coin_min_ask) > ctf.most_recent_sell_trade(trading_pair) and ctf.id_sell_order(trading_pair):
            time.sleep(.5)

    if emergency_mode:
        rerun_counter = 0
        while ctf.am_i_the_ask_leader(trading_pair, coin_min_ask) is True and rerun_counter != 100:
            print("I am the ask leader")
            time.sleep(.25)
            rerun_counter += 1

    try:
        ctf.exchange.cancel_order(ctf.id_sell_order(trading_pair), symbol=trading_pair)
    except TypeError:
        print("No open orders, running again.")
        market_seller()
    except OrderNotFound:
        print("order not found, running again")
        market_seller()
    print("order successfully canceled, running again")
    market_seller()


market_seller()