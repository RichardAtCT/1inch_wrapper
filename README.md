# 1inch.py

![1inch.py](https://raw.githubusercontent.com/RichardAtCT/1inch_wrapper/master/1inchpy.png)

1inch.py is a wrapper around the 1inch API and price Oracle. It has full coverage of the swap API endpoint and All chains support by 1inch are included in the OneInchSwap and OneInchOracle methods. 
Package also includes a helper method to ease the submission of transactions to the network. Limited chains currently supported. 

## API Documentation
The full 1inch swap API docs can be found at https://docs.1inch.io/
## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install 1inch.py.

```bash
pip install 1inch.py
```

## Usage

```python
from oneinch_py import OneInchSwap, TransactionHelper, OneInchOracle

rpc_url = "yourRPCURL.com"
binance_rpc = "adifferentRPCurl.com"
public_key = "yourWalletAddress"
private_key = "yourPrivateKey" #remember to protect your private key. Using environmental variables is recommended. 

exchange = OneInchSwap(public_key)
bsc_exchange = OneInchSwap(public_key, chain='binance')
helper = TransactionHelper(rpc_url, public_key, private_key)
bsc_helper = TransactionHelper(binance_rpc, public_key, private_key, chain='binance')
oracle = OneInchOracle(rpc_url, chain='ethereum')

# See chains currently supported by the helper method:
helper.chains
# {"ethereum": "1", "binance": "56", "polygon": "137", "avalanche": "43114"}

# Straight to business:
# Get a swap and do the swap
result = exchange.get_swap("USDT", "ETH", 10, 0.5) # get the swap transaction
result = helper.build_tx(result) # prepare the transaction for signing, gas price defaults to fast.
result = helper.sign_tx(result) # sign the transaction using your private key
result = helper.broadcast_tx(result) #broadcast the transaction to the network and wait for the receipt. 

#USDT to ETH price on the Oracle. Note that you need to indicate the token decimal if it is anything other than 18.
oracle.get_rate_to_ETH("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", src_token_decimal=6)

# Get the rate between any two tokens.
oracle.get_rate(src_token="0x6B175474E89094C44Da98b954EedeAC495271d0F", dst_token="0x111111111117dC0aa78b770fA6A738034120C302")

exchange.health_check()
# 'OK'

# Address of the 1inch router that must be trusted to spend funds for the swap
exchange.get_spender()

# Generate data for calling the contract in order to allow the 1inch router to spend funds. Token symbol or address is required. If optional "amount" variable is not supplied (in ether), unlimited allowance is granted.
exchange.get_approve("USDT")
exchange.get_approve("0xdAC17F958D2ee523a2206206994597C13D831ec7", amount=100)

# Get the number of tokens (in Wei) that the router is allowed to spend. Option "send address" variable. If not supplied uses address supplied when Initialization the exchange object. 
exchange.get_allowance("USDT")
exchange.get_allowance("0xdAC17F958D2ee523a2206206994597C13D831ec7", send_address="0x12345")

# Token List is stored in memory
exchange.tokens
# {
#  '1INCH': {'address': '0x111111111117dc0aa78b770fa6a738034120c302',
#            'decimals': 18,
#            'logoURI': 'https://tokens.1inch.exchange/0x111111111117dc0aa78b770fa6a738034120c302.png',
#            'name': '1INCH Token',
#            'symbol': '1INCH'},
#   'ETH': {'address': '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
#          'decimals': 18,
#          'logoURI': 'https://tokens.1inch.exchange/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png',
#          'name': 'Ethereum',
#          'symbol': 'ETH'},
#   ......
# }

# Returns the exchange rate of two tokens. 
# Tokens can be provided as symbols or addresses
# "amount" is supplied in ether
# NOTE: When using custom tokens, the token decimal is assumed to be 18. If your custom token has a different decimal - please manually pass it to the function (decimal=x)
# Also returns the "price" of more expensive token in the cheaper tokens. Optional variables can be supplied as **kwargs
exchange.get_quote(from_token_symbol='ETH', to_token_symbol='USDT', amount=1)
# (
#     {
#         "fromToken": {
#             "symbol": "ETH",
#             "name": "Ethereum",
#             "decimals": 18,
#             "address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
#             "logoURI": "https://tokens.1inch.io/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png",
#             "tags": ["native"],
#         },
#         "toToken": {
#             "symbol": "USDT",
#             "name": "Tether USD",
#             "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
#             "decimals": 6,
#             "logoURI": "https://tokens.1inch.io/0xdac17f958d2ee523a2206206994597c13d831ec7.png",
#             "tags": ["tokens"],
#         ...
#     Decimal("1076.503093"),
# )

# Creates the swap data for two tokens.
# Tokens can be provided as symbols or addresses
# Optional variables can be supplied as **kwargs
# NOTE: When using custom tokens, the token decimal is assumed to be 18. If your custom token has a different decimal - please manually pass it to the function (decimal=x)

exchange.get_swap(from_token_symbol='ETH', to_token_symbol='USDT', amount=1, slippage=0.5)
# {
#     "fromToken": {
#         "symbol": "ETH",
#         "name": "Ethereum",
#         "decimals": 18,
#         "address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
#         "logoURI": "https://tokens.1inch.io/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png",
#         "tags": ["native"],
#     },
#     "toToken": {
#         "symbol": "USDT",
#         "name": "Tether USD",
#         "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
#         "decimals": 6,
#         "logoURI": "https://tokens.1inch.io/0xdac17f958d2ee523a2206206994597c13d831ec7.png",
#         "tags": ["tokens"],
#
#     ...
#
#     ],
#     "tx": {
#         "from": "0x1d05aD0366ad6dc0a284C5fbda46cd555Fb4da27",
#         "to": "0x1111111254fb6c44bac0bed2854e76f90643097d",
#         "data": "0xe449022e00000000000000000000000000000000000000000000000006f05b59d3b20000000000000000000000000000000000000000000000000000000000001fed825a0000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000140000000000000000000000011b815efb8f581194ae79006d24e0d814b7697f6cfee7c08",
#         "value": "500000000000000000",
#         "gas": 178993,
#         "gasPrice": "14183370651",
#     },
# }


```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## License
[MIT](https://choosealicense.com/licenses/mit/)