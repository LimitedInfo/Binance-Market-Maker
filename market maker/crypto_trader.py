import ccxt
import re
import pandas as pd
import json
import time
from IPython.display import display
import config

# Takes a set of three trading pairs as input, in the list of strings format.
# or takes nothing and searches for arbitrage for all combinations of trading pairs.
input_list_string = input("Enter Complete scan or individual scan: ")
base_currencies_num = int(input("Enter number of base currencies desired (def = 10): "))
quote_currencies_num = int(input("Enter number of quote currencies desired (def = 5): "))

if not base_currencies_num:
    base_currencies_num = 10

if not quote_currencies_num:
    quote_currencies_num = 5

# converts inputted string to list
if len(input_list_string) > 1:
    input_list_string = input_list_string.replace('\'', '\"')
    print(input_list_string)
    input_list_string = json.loads(input_list_string)

# get exchange information for binance
exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': config.api_key,
    'secret': config.api_secret,
    'timeout': 30000,
    'enableRateLimit': True,
})


def make_order(ask_price_last, symbol_list, percent_purchase, direction):
    """
    multiplication goes from base symbol to quote symbol
    :param ask_price_last: asking price for
    :param symbol_list:
    :param percent_purchase:
    :param direction:
    :return:
    """
    if direction == 'forward':
        foo = re.search("/", symbol_list[0])
        coin_one = symbol_list[0][:foo.start()]

        foo = re.search("/", symbol_list[1])
        coin_two = symbol_list[1][:foo.start()]

        foo = re.search("/", symbol_list[2])
        coin_three = symbol_list[2][foo.end():]

        balance = exchange.fetch_balance()[coin_one]['free'] * percent_purchase
        print(balance)

        order = exchange.create_order(symbol_list[0], type='market', side='sell', amount=balance)

        balance = exchange.fetch_balance()[coin_two]['free']

        print(balance)
        order1 = exchange.create_order(symbol_list[1], type='market', side='sell', amount=balance)

        balance = exchange.fetch_balance()[coin_three]['free']
        amount = balance / ask_price_last

        print(balance)
        order2 = exchange.create_market_buy_order(symbol_list[2], amount=amount)
    if direction == 'backwards':
        foo = re.search("/", symbol_list[0])
        coin_one = symbol_list[0][:foo.start()]

        foo = re.search("/", symbol_list[1])
        coin_two = symbol_list[1][:foo.start()]

        foo = re.search("/", symbol_list[2])
        coin_three = symbol_list[2][foo.end():]

        balance = exchange.fetch_balance()[coin_one]['free'] * percent_purchase
        print(balance)

        order = exchange.create_order(symbol_list[0], type='market', side='sell', amount=balance)

        balance = exchange.fetch_balance()[coin_two]['free']

        print(balance)
        order1 = exchange.create_order(symbol_list[1], type='market', side='sell', amount=balance)

        balance = exchange.fetch_balance()[coin_three]['free']
        amount = balance / ask_price_last

        print(balance)
        order2 = exchange.create_market_buy_order(symbol_list[2], amount=amount)


binance_markets = exchange.load_markets()
# print(exchange.symbols)

c_pairs = list(binance_markets.keys())
# c_pairs_eth = list(filter(lambda x: "ETH" in x, c_pairs))[:10]


# takes a list of coin pairs (i.e. 'BTC/ETH') and appends
# the base (BTC) to a base list and the quote (ETH) to the quote list.

c_symbols = {}
base_currencies = []
quote_currencies = []

for c_pair in c_pairs:
    foo = re.search("/", c_pair)
    base_currency = c_pair[:foo.start()]
    quote_currency = c_pair[foo.end():]

    if base_currency not in base_currencies:
        base_currencies.append(base_currency)

    if quote_currency not in quote_currencies:
        quote_currencies.append(quote_currency)


# takes the base_currency list and the quote currency list.
# finds all combinations in these lists that result back into the same coin.

arb_formula_lists = []
for base_currency in base_currencies[:base_currencies_num]:
    for quote_currency in quote_currencies[:quote_currencies_num]:
        if base_currency != quote_currency:
            for quote_currency1 in quote_currencies[:quote_currencies_num]:
                if quote_currency != quote_currency1 and base_currency != quote_currency1:
                    arb_formula_lists.append(
                        [base_currency + '/' + quote_currency, quote_currency + '/' + quote_currency1,
                         base_currency + '/' + quote_currency1])


# ['EOS/ETH', 'ETH/USDC', 'EOS/USDC'] format of our trading pairs list.
# if changing to base then use ask, if changing to quote then use bid.
# if we are changing to base then multiply, if changing to quote then divide.

def arb_profit_f(arb_cross_cur):
    c_spreads = {}
    for c_pair in arb_cross_cur:
        try:
            orderbook = exchange.fetch_order_book(c_pair, limit=5)
        except:
            return None
        bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
        ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
        spread = (ask - bid) if (bid and ask) else None
        c_spreads[c_pair] = [bid, ask, spread]
        # time.sleep(wait)

    res = list(c_spreads.keys())
    # df = pd.DataFrame.from_dict(c_spreads, orient='index', columns=['Bid', 'Ask', 'Spread'])
    try:
        return c_spreads[res[0]][1] * c_spreads[res[1]][0] * (c_spreads[res[2]][1] ** -1), \
               c_spreads[res[0]][1] * c_spreads[res[1]][0] * (c_spreads[res[2]][1] ** -1), \
               arb_cross_cur, c_spreads

    except:
        return None

    # return ((df.iloc[0, 0] * (df.iloc[1, 0]) * (df.iloc[2, 1] ** -1)), arb_cross_cur, df)


if not input_list_string:

    arb_profit = {}
    for arb_symbols in arb_formula_lists:
        print(arb_symbols)
        foo = arb_profit_f(arb_symbols)
        if foo is None:
            continue

        arb_profit[str(foo[2])] = foo[0], foo[1], foo[3]

    df1 = pd.DataFrame.from_dict(arb_profit, orient='index', columns=['Profit', 'Profit1', 'Prices'])
    display(df1['Profit'])
    bool_symbol_sets = df1['Profit'] > .9

    df1_potential_profit = df1[bool_symbol_sets]

    symbol_sets_lists = []
    for index, series in df1_potential_profit.iterrows():
        print(index)
        string_list = index.replace('\'', '\"')
        print(string_list)
        symbol_sets_lists.append(json.loads(string_list))

    count = 0
    counter = 0

    while count == 0:
        for symbol_set in symbol_sets_lists:
            profit_info = arb_profit_f(symbol_set)
            if profit_info[0] > 1.004 or profit_info[1] < .996:
                print(profit_info)
                print(exchange.fetch_ticker(symbol_set[0]))
                time.sleep(200)
                # if profit_info[0] > 1.00225:
                #     # make_order(profit_info[3][profit_info[2][-1]][1], profit_info[2], .999, 'forward')
                # if profit_info[0] < .99775:
                    # make_order(profit_info[3][profit_info[2][-1]][1], profit_info[2], .999, 'backward')

            counter += 1
            if counter % 200 == 0:
                print("200 tests done")


else:
    arb_profit = {}

    foo = arb_profit_f(input_list_string)

    arb_profit[str(foo[1])] = foo[0], foo[2]

    df1 = pd.DataFrame.from_dict(arb_profit, orient='index', columns=['Profit', 'Prices'])
    # display(df1)
    print(df1.mean(), df1.max(), df1.min())

    count = 0
    while count == 0:
        profit_info = arb_profit_f(input_list_string)
        if profit_info[0] > 1.003:
            print("order made!")
            make_order(profit_info[2][input_list_string[-1]][1], input_list_string, .999)
        print("not less than")
        time.sleep(10)

    # if df1['Profit'] < .995:
    #     exchange.or