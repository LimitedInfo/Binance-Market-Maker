import sys
import time

sys.path.append(r'C:\Users\Andrew\PycharmProjects\old computer projects\cryptotrader\market maker')

import crypto_trader_functions as ctf
# from crypto_trader_functions import exchange

def main():
    balance_to_buy = 1
    stop_price = .95 #decline to initiate panic sell
    sell_at_loss_price = .89 #change from initial purchase to sell at
    multipliers = [1.185, 1.385, 1.685, 1.9, 2.45, 2.85]

    # tradingpair = sys.argv[1].upper()


    # print(ctf.free_balance('ETH/BTC'))
    # print(ctf.true_bid(tradingpair, .5))

    quantity_to_buy_eth = (ctf.free_balance('BNB/ETH')['Quote'] * balance_to_buy)
    quantity_to_buy_btc = (ctf.free_balance('ETH/BTC')['Quote'] * balance_to_buy)
    quantity_to_buy_usdt = (ctf.free_balance('BTC/USDT')['Quote'] * balance_to_buy)
    quantity_to_buy_bnb = (ctf.free_balance('CAKE/BNB')['Quote'] * balance_to_buy)
    # smh

    tradingpair = input('please input trading symbol (ex. eth): ').upper()
    tradingpair = tradingpair[:3] + '/' + 'BTC'
    quote = tradingpair[4:]

    start_time = time.time()
    # amount isn't used here, despite it being required by the function. "quoteOrderQty" is amount in this case.

    if quote == 'BTC':
        ctf.exchange.create_order(symbol=tradingpair, type='market', side='buy', params={'quoteOrderQty': quantity_to_buy_btc},
                                  amount=quantity_to_buy_btc,)
    elif quote == 'USDT':
        ctf.exchange.create_order(symbol=tradingpair, type='market', side='buy', params={'quoteOrderQty': quantity_to_buy_usdt},
                                  amount=quantity_to_buy_usdt,)
    elif quote == 'ETH':
        ctf.exchange.create_order(symbol=tradingpair, type='market', side='buy', params={'quoteOrderQty': quantity_to_buy_eth},
                                  amount=quantity_to_buy_eth,)
    elif quote == 'BNB':
        ctf.exchange.create_order(symbol=tradingpair, type='market', side='buy', params={'quoteOrderQty': quantity_to_buy_bnb},
                                  amount=quantity_to_buy_bnb,)


    first_trade = time.time() - start_time

    true_bid = ctf.true_bid(tradingpair, 0)
    first_price = true_bid
    limit_order_size = ctf.free_balance(tradingpair)['Base'] / len(multipliers)

    for multiplier in multipliers:
        ctf.exchange.create_order(symbol=tradingpair, type='limit', side='sell',
                                  amount=limit_order_size,
                                  price=true_bid * multiplier)

    last_trade = time.time() - start_time
    print(first_trade)
    print(last_trade)

    while True:
        print('------ checking if we should panic sell (ctrl+c in terminal to stop checks) ------')
        if ctf.true_bid(tradingpair,0) < first_price*sell_at_loss_price:
            ctf.exchange.cancel_all_orders(symbol=tradingpair)

            ctf.exchange.create_order(symbol=tradingpair, type='stop_loss_limit', side='sell',
                                      amount=ctf.free_balance(tradingpair)['Base'],
                                      price=true_bid * sell_at_loss_price,
                                      params={'stopPrice': true_bid*stop_price, 'timeInForce': 'GTC'})

        time.sleep(1)







if __name__ == '__main__':
    main()