import ccxt
import time
import crypto_trader_functions as ctf
import config

exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': config.api_key,
    'secret': config.api_secret,
    'timeout': 30000,
    'enableRateLimit': True,
})
_since = int(round(time.time() * 1000)) - 1200000
trading_pair = 'OMG/ETH'

def any_open_orders_buy(trading_pair):
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

# print(exchange.fetch_trades(trading_pair)[-2:])
# print(exchange.fetch_closed_orders(trading_pair)[-2])
coin_min_bid = ctf.coin_min(trading_pair, multiplier=.2)
coin_min_ask = ctf.coin_min(trading_pair, multiplier=.8)

# print(ctf.coin_min(trading_pair))
# print(ctf.exchange.fetch_trades(trading_pair, since=_since))
# print(ctf.target_sell_price(trading_pair, .003))
print(ctf.most_recent_sell_trade(trading_pair))