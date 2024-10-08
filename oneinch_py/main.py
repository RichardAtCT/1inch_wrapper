import json
import time

import requests
from web3 import Web3
import importlib.resources as pkg_resources

from web3.exceptions import ExtraDataLengthError
from web3.middleware import ExtraDataToPOAMiddleware


class UnknownToken(Exception):
    pass


class OneInchSwap:
    base_url = 'https://api.1inch.dev/swap'
    api_key = ''

    version = {
        "v5.2": "v5.2"
    }

    chains = {
        "ethereum": "1",
        "binance": "56",
        "polygon": "137",
        "optimism": "10",
        "arbitrum": "42161",
        "gnosis": "100",
        "avalanche": "43114",
        "fantom": "250",
        "klaytn": "8217",
        "aurora": "1313161554",
        "zksync": "324"
    }

    def __init__(self, api_key, address, chain='ethereum', version='v5.2'):
        self.presets = None
        self.tokens = {}
        self.tokens_by_address = {}
        self.protocols = []
        self.address = address
        self.api_key = api_key
        self.version = version
        self.chain_id = self.chains[chain]
        self.chain = chain
        self.tokens = self.get_tokens()
        time.sleep(1)
        self.spender = self.get_spender()
        time.sleep(1)

   
    def _get(self, url, params=None, headers=None):
        """ Implements a get request """
        try:
            if headers is None:
                headers = {"accept": "application/json", "Authorization": f"Bearer {self.api_key}"}
            else:
                headers["accept"] = "application/json"
                headers["Authorization"] = f"Bearer {self.api_key}"
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.ConnectionError as e:
            # error_content = json.loads(e.response._content.decode("utf-8"))
            print(f"ConnectionError with code {e.response.status_code} when doing a GET request from {format(url)}")
            # print(f"{error_content['error']} {error_content['description']}")
            payload = None
        except requests.exceptions.HTTPError as e:
            # error_content = json.loads(e.response._content.decode("utf-8"))
            print(f"HTTPError with code {e.response.status_code} for a request {format(url)}")
            # print(f"{error_content['error']} {error_content['description']}")
            payload = None
        return payload

    def _token_to_address(self, token: str):
        if len(token) == 42:
            return Web3.to_checksum_address(token)
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
        self.spender = result
        return self.spender

    def get_tokens(self):
        """
        Calls the Tokens API endpoint
        :return: A dictionary of all the whitelisted tokens.
        """
        url = f'https://api.1inch.dev/token/v1.2/{self.chain_id}'
        result = self._get(url)
        for key in result:
            token = result[key]
            self.tokens_by_address[key] = token
            self.tokens[token['symbol']] = token
        return self.tokens
    
    def get_liquidity_sources(self):
        url = f'{self.base_url}/{self.version}/{self.chain_id}/liquidity-sources'
        result = self._get(url)
        self.protocols = result
        return self.protocols

    def get_presets(self):
        url = f'{self.base_url}/{self.version}/{self.chain_id}/presets'
        result = self._get(url)
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
        if decimal == 0:
            amount_in_wei = int(amount)
        else:
            amount_in_wei = int(amount * 10 ** decimal)
        url = f'{self.base_url}/{self.version}/{self.chain_id}/quote'
        url = url + f'?src={from_address}&dst={to_address}&amount={amount_in_wei}'
        if kwargs is not None:
            result = self._get(url, params=kwargs)
        else:
            result = self._get(url)
        # from_base = Decimal(result['fromTokenAmount']) / Decimal(10 ** result['fromToken']['decimals'])
        # to_base = Decimal(result['toTokenAmount']) / Decimal(10 ** result['toToken']['decimals'])
        # if from_base > to_base:
        #     rate = from_base / to_base
        # else:
        #     rate = to_base / from_base
        return result

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
        if decimal == 0:
            amount_in_wei = int(amount)
        else:
            amount_in_wei = int(amount * 10 ** decimal)
        url = f'{self.base_url}/{self.version}/{self.chain_id}/swap'
        url = url + f'?src={from_address}&dst={to_address}&amount={amount_in_wei}'
        url = url + f'&from={send_address}&slippage={slippage}'
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

    def get_approve(self, from_token_symbol: str, amount=None, decimal=None):
        from_address = self._token_to_address(from_token_symbol)
        if decimal is None:
            try:
                self.tokens[from_token_symbol]['decimals']
            except KeyError:
                decimal = 18
            else:
                decimal = self.tokens[from_token_symbol]['decimals']
        else:
            pass
        url = f'{self.base_url}/{self.version}/{self.chain_id}/approve/transaction'
        if amount is None:
            url = url + f"?tokenAddress={from_address}"
        else:
            if decimal == 0:
                amount_in_wei = int(amount)
            else:
                amount_in_wei = int(amount * 10 ** decimal)
            url = url + f"?tokenAddress={from_address}&amount={amount_in_wei}"
        result = self._get(url)
        return result


class TransactionHelper:
    gas_oracle = "https://gas-price-api.1inch.io/v1.3/"

    chains = {
        "ethereum": "1",
        "binance": "56",
        "polygon": "137",
        "optimism": "10",
        "arbitrum": "42161",
        "gnosis": "100",
        "avalanche": "43114",
        "fantom": "250",
        "klaytn": "8217",
        "aurora": "1313161554",
        "zksync": "324"
    }

    abi = json.loads(pkg_resources.read_text(__package__, 'erc20.json'))['result']
    abi_aggregator = json.loads(pkg_resources.read_text(__package__, 'aggregatorv5.json'))['result']

    def _get(self, url, params=None, headers=None):
        """ Implements a get request """
        try:
            if headers is None:
                headers = {"accept": "application/json", "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            else:
                headers["accept"] = "application/json"
                headers["Authorization"] = f"Bearer {self.api_key}"
                headers["Content-Type"] = "application/json"
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.ConnectionError as e:
            # error_content = json.loads(e.response._content.decode("utf-8"))
            print("ConnectionError: %s when doing a GET request from {}".format(url) % e)
            # print(f"{error_content['error']} {error_content['description']}")
            payload = None
        except requests.exceptions.HTTPError:
            # error_content = json.loads(e.response._content.decode("utf-8"))
            print("HTTPError {}".format(url))
            # print(f"{error_content['error']} {error_content['description']}")
            payload = None
        return payload


    @staticmethod
    def test_poa_chain(ins: Web3) -> bool:
        try:
            ins.eth.get_block('latest', True)
        except ExtraDataLengthError:
            return True
        return False

    def __init__(self,  api_key, rpc_url, public_key, private_key, chain='ethereum', broadcast_1inch=False):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if self.test_poa_chain(self.w3):
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        else:
            pass
        self.api_key =  api_key
        self.public_key = public_key
        self.private_key = private_key
        self.chain = chain
        self.chain_id = self.chains[chain]
        self.broadcast_1inch = broadcast_1inch

    def build_tx(self, raw_tx, speed='high'):
        nonce = self.w3.eth.get_transaction_count(self.public_key)
        if raw_tx is None:
            return None
        if 'tx' in raw_tx:
            tx = raw_tx['tx']
        else:
            tx = raw_tx
        if 'from' not in tx:
            tx['from'] = self.w3.to_checksum_address(self.public_key)
        tx['to'] = self.w3.to_checksum_address(tx['to'])
        if 'gas' not in tx:
            tx['gas'] = self.w3.eth.estimate_gas(tx)
        tx['nonce'] = nonce
        tx['chainId'] = int(self.chain_id)
        tx['value'] = int(tx['value'])
        tx['gas'] = int(tx['gas'] * 1.25)
        if self.chain == 'ethereum' or self.chain == 'polygon' or self.chain == 'avalanche' or self.chain == 'gnosis' or self.chain == 'klaytn':
            gas = self.get_gas_prices()
            tx['maxPriorityFeePerGas'] = int(gas[speed]['maxPriorityFeePerGas'])
            tx['maxFeePerGas'] = int(gas[speed]['maxFeePerGas'])
            tx.pop('gasPrice')
        else:
            tx['gasPrice'] = int(tx['gasPrice'])
        return tx
    
    def get_gas_prices(self):
        return self._get(self.gas_oracle + self.chain_id)

    def sign_tx(self, tx):
        if tx is None:
            return None
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        return signed_tx

    def broadcast_tx(self, signed_tx, timeout=360):
        api_base_url = 'https://api.1inch.dev/tx-gateway/v1.1/'
        api_headers = {"accept": "application/json", "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        if signed_tx is None:
            return None
        if self.broadcast_1inch is True:
            tx_json = signed_tx.rawTransaction
            tx_json = {"rawTransaction": tx_json.hex()}
            payload = requests.post(api_base_url + self.chain_id + "/broadcast", data=self.w3.to_json(tx_json), headers=api_headers)
            tx_hash = json.loads(payload.text)
            tx_hash = tx_hash['transactionHash']
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            return receipt, tx_hash
        else:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(tx_hash.hex())
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            return receipt, tx_hash.hex()

    def get_erc20_balance(self, contract_address, decimal=None):
        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(contract_address), abi=self.abi)
        balance_in_wei = contract.functions.balanceOf(self.public_key).call()
        if decimal is None:
            return self.w3.from_wei(balance_in_wei, 'ether')
        elif decimal == 0:
            return balance_in_wei
        else:
            return balance_in_wei / 10 ** decimal

    def decode_abi(self, transaction):
        contract = self.w3.eth.contract(address=self.w3.to_checksum_address('0x1111111254EEB25477B68fb85Ed929f73A960582'), abi=self.abi_aggregator)
        data = transaction['tx']['data']
        decoded_data = contract.decode_function_input(data)
        return decoded_data


class OneInchOracle:
    chains = {
        "ethereum": "1",
        "binance": "56",
        "polygon": "137",
        "optimism": "10",
        "arbitrum": "42161",
        "gnosis": "100",
        "avalanche": "43114",
        "fantom": "250",
        "klaytn": "8217",
        "aurora": "1313161554",
        "zksync": "324"
    }

    contracts = {
        "ethereum": '0x07D91f5fb9Bf7798734C3f606dB065549F6893bb',
        "binance": '0xfbD61B037C325b959c0F6A7e69D8f37770C2c550',
        "polygon": "0x7F069df72b7A39bCE9806e3AfaF579E54D8CF2b9",
        "optimism": "0x11DEE30E710B8d4a8630392781Cc3c0046365d4c",
        "arbitrum": "0x735247fb0a604c0adC6cab38ACE16D0DbA31295F",
        "gnosis": "0x142DB045195CEcaBe415161e1dF1CF0337A4d02E",
        "avalanche": "0xBd0c7AaF0bF082712EbE919a9dD94b2d978f79A9",
        "fantom": "0xE8E598A1041b6fDB13999D275a202847D9b654ca",
        "zksync": "0xC762d56614D3411eC6fABD56cb075D904b801613"
    }

    # multicall_address = "0xDA3C19c6Fe954576707fA24695Efb830D9ccA1CA"

    oracle_abi = json.loads(pkg_resources.read_text(__package__, 'oracle.json'))['result']
    # multicall_abi = json.loads(pkg_resources.read_text(__package__, 'multicall.json'))['result']

    def __init__(self, rpc_url, chain='ethereum'):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain = chain
        self.chain_id = self.chains[chain]
        self.contract_address = self.contracts[chain]
        self.oracle_contract = self.w3.eth.contract(address=self.contract_address, abi=self.oracle_abi)
        # self.multicall_contract = self.w3.eth.contract(address=self.multicall_address, abi=self.multicall_abi)

    def get_rate(self, src_token, dst_token, wrap=False, src_token_decimal: int = 18, dst_token_decimal: int = 18):
        rate = self.oracle_contract.functions.getRate(self.w3.to_checksum_address(src_token),
                                                      self.w3.to_checksum_address(dst_token), wrap).call()
        if src_token_decimal == 18 and dst_token_decimal < 18:
            rate = rate / 10 ** dst_token_decimal
        elif dst_token_decimal == 18 and src_token_decimal < 18:
            rate = rate / 10 ** ((18 - src_token_decimal) + 18)
        elif dst_token_decimal < 18 and src_token_decimal < 18:
            rate = rate / 10 ** ((18 - src_token_decimal) + (18 - dst_token_decimal))
        else:
            rate = rate / 10 ** 18
        return rate

    def get_rate_to_eth(self, src_token, wrap=False, src_token_decimal=18):
        rate = self.oracle_contract.functions.getRateToEth(self.w3.to_checksum_address(src_token), wrap).call()
        if src_token_decimal == 18:
            rate = rate / 10 ** 18
        elif src_token_decimal < 18:
            rate = rate / 10 ** ((18 - src_token_decimal) + 18)
        return rate
# TODO Figure this all out at some point
    # def get_multicall(self, token_list):
    #     for address in token_list:
    #         call_data = {
    #             "to": "0x07D91f5fb9Bf7798734C3f606dB065549F6893bb",
    #             "data": f"{self.oracle_contract.functions.getRateToEth(address,True)}"
    #         }
    #
    #     print(call_data)
    #     # mapped = map(lambda , token_list, wrap_list)
    #     # mapped = list(mapped)
    #     # rate = self.multicall_contract.functions.multicall(mapped).call()
    #     return


if __name__ == '__main__':
    pass
