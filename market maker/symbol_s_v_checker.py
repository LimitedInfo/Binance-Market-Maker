import ccxt
import pandas as pd
from IPython.display import display
import numpy as np
import re
import matplotlib.pyplot as plt
import config

exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': config.api_key,
    'secret': config.api_secret,
    'timeout': 30000,
    'enableRateLimit': True,
})

def total_volume(symbol, base_volume, quote_volume, vwap):
    index = re.search("/", symbol)
    base = symbol[:index.start()]
    quote = symbol[index.end():]
    total_volume = quote_volume

    try:
        quote_to_usd = exchange.fetch_ticker(quote + '/USDT')['last']
    except:
        return np.NaN

    return quote_to_usd * total_volume



binance_markets = exchange.load_markets()

c_pairs = list(binance_markets.keys())

tickers_df = pd.DataFrame.from_dict(exchange.fetch_tickers(c_pairs[:40]))
tickers_df.replace(0, np.nan, inplace=True)
#
# display(tickers_df.loc['bid'])
#
# print(tickers_df.loc['ask'] / tickers_df.loc['bid'])
# print('SNT/ETH', tickers_df.loc['baseVolume', 'SNT/ETH'], tickers_df.loc['quoteVolume', 'SNT/ETH'], tickers_df.loc[ 'vwap', 'SNT/ETH'])

volume_spread_dict = {}
for c_pair in c_pairs[:40]:
    volume_spread_dict[c_pair] = [total_volume(c_pair, tickers_df.loc['baseVolume', c_pair], tickers_df.loc['quoteVolume', c_pair], tickers_df.loc['vwap', c_pair]), tickers_df.loc['ask', c_pair]/tickers_df.loc['bid', c_pair]]


volume_spread_df = pd.DataFrame.from_dict(volume_spread_dict, orient='index', columns=['volume', 'spread'])
display(volume_spread_df)

volume_spread_df.plot(kind='scatter', x='volume', y='spread', color='purple')
plt.show()

# print(volume_spread_dict)

# for key in volume_spread_dict.keys():
#     plt.plot(volume_spread_dict[key][0], volume_spread_dict[key][1])
#     plt.show()
#     input('press enter to continue')

# print(exchange.fetch_trades('SNT/ETH', limit=10))
