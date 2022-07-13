import requests
import web3
from decimal import *


class UnknownToken(Exception):
    pass


class OneInchSwap:
    base_url = 'https://api.1inch.exchange'

    version = {
        "v4.0": "v4.0"
    }

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

    def __init__(self, address, chain='ethereum', version='v4.0'):
        self.presets = None
        self.tokens = {}
        self.tokens_by_address = {}
        self.protocols = []
        self.address = address
        self.version = version
        self.chain_id = self.chains[chain]
        self.chain = chain
        self.tokens = self.get_tokens()
        self.spender = self.get_spender()

    @staticmethod
    def _get(url, params=None, headers=None):
        """ Implements a get request """
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.ConnectionError as e:
            print("ConnectionError when doing a GET request from {}".format(url))
            payload = None
        except requests.exceptions.HTTPError:
            print("HTTPError {}".format(url))
            payload = None
        return payload

    def _token_to_address(self, token: str):
        if len(token) == 42:
            return token
        else:
            try:
                address = self.tokens[token]['address']
            except:
                raise UnknownToken("Token not in 1inch Token List")
            return address

    def health_check(self):
        """
        Calls the Health Check Endpoint
        :return: Always returns code 200 if API is stable
        """
        url = f'{self.base_url}/{self.version}/{self.chain_id}/healthcheck'
        response = self._get(url)
        return response['status']

    def get_spender(self):
        url = f'{self.base_url}/{self.version}/{self.chain_id}/approve/spender'
        result = self._get(url)
        if not result.__contains__('spender'):
            return result
        self.spender = result
        return self.spender

    def get_tokens(self):
        """
        Calls the Tokens API endpoint
        :return: A dictionary of all the whitelisted tokens.
        """
        url = f'{self.base_url}/{self.version}/{self.chain_id}/tokens'
        result = self._get(url)
        if not result.__contains__('tokens'):
            return result
        for key in result['tokens']:
            token = result['tokens'][key]
            self.tokens_by_address[key] = token
            self.tokens[token['symbol']] = token
        return self.tokens

    def get_liquidity_sources(self):
        url = f'{self.base_url}/{self.version}/{self.chain_id}/liquidity-sources'
        result = self._get(url)
        if not result.__contains__('liquidity-sources'):
            return result
        self.protocols = result
        return self.protocols

    def get_presets(self):
        url = f'{self.base_url}/{self.version}/{self.chain_id}/presets'
        result = self._get(url)
        if not result.__contains__('presets'):
            return result
        self.presets = result
        return self.presets

    def get_quote(self, from_token_symbol: str, to_token_symbol: str, amount: float, decimal=None, **kwargs):
        """
        Calls the QUOTE API endpoint. NOTE: When using custom tokens, the token decimal is assumed to be 18. If your
        custom token has a different decimal - please manually pass it to the function (decimal=x)
        """
        from_address = self._token_to_address(from_token_symbol)
        to_address = self._token_to_address(to_token_symbol)
        if decimal is None:
            try:
                self.tokens[from_token_symbol]['decimals']
            except KeyError:
                decimal = 18
            else:
                decimal = self.tokens[from_token_symbol]['decimals']
        else:
            pass
        amount_in_wei = Decimal(amount * 10 ** decimal)
        url = f'{self.base_url}/{self.version}/{self.chain_id}/quote'
        url = url + f'?fromTokenAddress={from_address}&toTokenAddress={to_address}&amount={amount_in_wei}'
        if kwargs is not None:
            result = self._get(url, params=kwargs)
        else:
            result = self._get(url)
        from_base = Decimal(result['fromTokenAmount']) / Decimal(10 ** result['fromToken']['decimals'])
        to_base = Decimal(result['toTokenAmount']) / Decimal(10 ** result['toToken']['decimals'])
        if from_base > to_base:
            rate = from_base / to_base
        else:
            rate = to_base / from_base
        return result, rate

    def get_swap(self, from_token_symbol: str, to_token_symbol: str,
                 amount: float, slippage: float, decimal=None, send_address=None, **kwargs):
        """
        Calls the SWAP API endpoint. NOTE: When using custom tokens, the token decimal is assumed to be 18. If your
        custom token has a different decimal - please manually pass it to the function (decimal=x)
        """
        if send_address is None:
            send_address = self.address
        else:
            pass
        from_address = self._token_to_address(from_token_symbol)
        to_address = self._token_to_address(to_token_symbol)
        if decimal is None:
            try:
                self.tokens[from_token_symbol]['decimals']
            except KeyError:
                decimal = 18
            else:
                decimal = self.tokens[from_token_symbol]['decimals']
        else:
            pass
        amount_in_wei = Decimal(amount * 10 ** decimal)
        url = f'{self.base_url}/{self.version}/{self.chain_id}/swap'
        url = url + f'?fromTokenAddress={from_address}&toTokenAddress={to_address}&amount={amount_in_wei}'
        url = url + f'&fromAddress={send_address}&slippage={slippage}'
        if kwargs is not None:
            result = self._get(url, params=kwargs)
        else:
            result = self._get(url)
        return result

    def get_allowance(self, from_token_symbol: str, send_address=None):
        if send_address is None:
            send_address = self.address
        from_address = self._token_to_address(from_token_symbol)
        url = f'{self.base_url}/{self.version}/{self.chain_id}/approve/allowance'
        url = url + f"?tokenAddress={from_address}&walletAddress={send_address}"
        result = self._get(url)
        return result

    def get_approve(self, from_token_symbol: str, amount=None):
        from_address = self._token_to_address(from_token_symbol)
        amount_in_wei = Decimal(amount * 10 ** self.tokens[from_token_symbol]['decimals'])
        url = f'{self.base_url}/{self.version}/{self.chain_id}/approve/transaction'
        url = url + f"?tokenAddress={from_address}&amount={amount_in_wei}"
        result = self._get(url)
        return result


if __name__ == '__main__':
    pass
