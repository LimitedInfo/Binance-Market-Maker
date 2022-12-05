import ccxt
import re
import time
import datetime
import pandas as pd
import numpy as np
import crypto_trader_functions as ctf


def market_seller(trading_pair, target_selling_price, coin_min_bid, coin_min_ask):
    try:
        print("in market seller")

        # TODO: base emergency selling on actual trade history, not current asking price.
        if ctf.true_ask(trading_pair, coin_min=coin_min_ask) < target_selling_price * .994:#exchange.fetch_ohlcv(trading_pair, timeframe='3m', limit=2)[-1][4] < target_selling_price * .99:
            print("state of emergency.")
            ctf.exchange.create_order(symbol=trading_pair, type='limit', side='sell',
                                      amount=ctf.free_balance(trading_pair)['Base'],
                                      price=ctf.true_ask(trading_pair, coin_min=coin_min_ask) * .999)
            state_of_emergency = 1
        else:
            print("normal target trade.")
            ctf.exchange.create_order(symbol=trading_pair, type='limit', side='sell',
                                      amount=ctf.free_balance(trading_pair)['Base'],
                                      price=target_selling_price * .9997)
            state_of_emergency = 0

        # TODO: make it so that seller is fine with not being leader, when not below target price.

        while True:
            if ctf.am_i_the_ask_leader(trading_pair, coin_min_ask) is False and state_of_emergency == 1:
                print("cancelling")
                ctf.exchange.cancel_order(ctf.id_sell_order(trading_pair), symbol=trading_pair)
                market_seller(trading_pair, target_selling_price, coin_min_bid, coin_min_ask)

            else:
                print("waiting.")
                time.sleep(15)
                if ctf.am_i_the_ask_leader(trading_pair, coin_min_ask) is False or ctf.exchange.fetch_open_orders(symbol=trading_pair)[0]['price'] <= ctf.true_ask(trading_pair, coin_min=coin_min_ask) * .996:
                    ctf.exchange.cancel_order(ctf.id_sell_order(trading_pair), symbol=trading_pair)
                    market_seller(trading_pair, target_selling_price, coin_min_bid, coin_min_ask)
    except ccxt.base.errors.InvalidOrder:
        return 1
    except UnboundLocalError:
        return 1
    except Exception as inst:
        print(type(inst))  # the exception instance
        print(inst.args)  # arguments stored in .args
        print(inst)






trading_pair = input("trading pair (e.x. SNT/ETH):")
if not trading_pair:
    trading_pair = 'SNT/ETH'


amount_to_sell = input("amount of target currency to sell: (e.x. 100):")
if not amount_to_sell:
    amount_to_sell = 100

spread = input("desired spread (e.x. .006):")
if not spread:
    spread = .006
if isinstance(spread, str):
    spread = float(spread)


coin_min_bid = ctf.coin_min(trading_pair, multiplier=.2)
coin_min_ask = ctf.coin_min(trading_pair, multiplier=.8)

print(ctf.target_sell_price(trading_pair, spread))

while True:
    if ctf.free_balance(trading_pair)['Base'] > 90:
        market_seller(trading_pair, target_selling_price=ctf.target_sell_price(trading_pair, spread),
                      coin_min_bid=coin_min_bid, coin_min_ask=coin_min_ask)
    print("waiting...")
    time.sleep(5)