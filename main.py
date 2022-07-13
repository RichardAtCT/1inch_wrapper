from oneinch_wrapper.main import OneInchSwap

chains = {
        "ethereum": '1',
        "binance": '56',
        "polygon": "137",
        "optimism": "10",
        "arbitrum": "42161",
        "gnosis": "100",
        "avalanche": "43114",
        "fantom": "250"
    }
for key in chains.keys():
    exchange = OneInchSwap('0x1d05aD0366ad6dc0a284C5fbda46cd555Fb4da27', chain=key)
    # print(key)
    # print(next(iter(exchange.tokens)))
    print(exchange.get_swap(from_token_symbol='ETH', to_token_symbol='USDT', amount=0.5, slippage=0.5))

# eth_exchange = OneInchSwap('0x1d05aD0366ad6dc0a284C5fbda46cd555Fb4da27')
# polygon_exchange = OneInchSwap('0x1d05aD0366ad6dc0a284C5fbda46cd555Fb4da27', chain="polygon")
#
# print(eth_exchange.tokens)
# print(polygon_exchange.tokens)
# print(eth_exchange.get_quote("ETH", "1INCH", 1)[1])
# print(polygon_exchange.get_quote("DAI", "ETH", 500)[1])
