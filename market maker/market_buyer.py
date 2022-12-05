import ccxt
import re
import time
import datetime
import pandas as pd
import numpy as np
import crypto_trader_functions as ctf

current_milli_time = lambda: int(round(time.time() * 1000))

def market_maker(trading_pair, coin_min_bid, coin_min_ask, amount_to_buy=100, spread=.006):
    print("in market maker")
    # if ctf.free_balance(trading_pair)['Quote'] / ctf.true_bid(trading_pair) > amount_to_buy:
    if ctf.true_spread(trading_pair, coin_min=coin_min_bid) > spread and ctf.hows_the_market_doing(trading_pair, price_dec_perc=.004) == 'good':
        print("greater than .006")

        try:
            ctf.exchange.create_order(symbol=trading_pair, type='limit', side='buy',
                                      amount=amount_to_buy,
                                      price=ctf.true_bid(trading_pair, coin_min=coin_min_bid) * 1.0005)
        except ccxt.base.errors.InsufficientFunds:
            return 1

        while ctf.am_i_the_bid_leader(trading_pair, coin_min_bid) is True and ctf.true_spread(trading_pair, coin_min=coin_min_bid) > spread:
            print("checking for leader position and spread.")

        print("not the bid leader")

        ctf.exchange.cancel_order(ctf.id_open_order(trading_pair), symbol=trading_pair)

        market_maker(trading_pair, coin_min_bid, coin_min_ask, amount_to_buy, spread)


        # time.sleep(10)

    else:
        print("spread insufficient or price is decreasing.")
        if ctf.hows_the_market_doing(trading_pair, price_dec_perc=.004) == 'good':
            not_leader_trade_price = ctf.true_ask(trading_pair, coin_min=coin_min_ask) * .993
            ctf.exchange.create_order(symbol=trading_pair, type='limit', side='buy',
                                      amount=amount_to_buy,
                                      price=not_leader_trade_price)

        while ctf.true_spread(trading_pair, coin_min=coin_min_bid) < spread and ctf.hows_the_market_doing(trading_pair, price_dec_perc=.004) == 'good':
            time.sleep(5)

        try:
            ctf.exchange.cancel_order(ctf.id_open_order(trading_pair), symbol=trading_pair)
        except:
            print("waiting for market to improve.")
            time.sleep(10)
            market_maker(trading_pair, coin_min_bid, coin_min_ask, amount_to_buy, spread)

        print("waiting for market to improve.")
        time.sleep(2)
        market_maker(trading_pair, coin_min_bid, coin_min_ask, amount_to_buy, spread)

    # else:
    #     print("insufficient balance - waiting...")
    #     time.sleep(15)
    #     market_maker(trading_pair)



trading_pair = input("trading pair (e.x. SNT/ETH):")
if not trading_pair:
    trading_pair = 'SNT/ETH'

spread = input("desired spread (e.x. .006):")
if not spread:
    spread = .006
if isinstance(spread, str):
    spread = float(spread)

amount_to_buy = input("amount of target currency to buy: (e.x. 100):")
if not amount_to_buy:
    amount_to_buy = 100
if isinstance(amount_to_buy, str):
    amount_to_buy = int(amount_to_buy)

coin_min_bid = ctf.coin_min(trading_pair, multiplier=.2)
coin_min_ask = ctf.coin_min(trading_pair, multiplier=.8)

market_maker(trading_pair, coin_min_bid, coin_min_ask, amount_to_buy=amount_to_buy, spread=spread)


