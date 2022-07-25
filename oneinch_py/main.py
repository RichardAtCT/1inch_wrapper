import json
import requests
from web3 import Web3
from decimal import *
import importlib.resources as pkg_resources
from functools import reduce
from web3.middleware import geth_poa_middleware


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


class TransactionHelper:

    gas_oracles = {
        # "ethereum": 'https://etherchain.org/api/gasnow',
        "binance": 'https://gbsc.blockscan.com/gasapi.ashx?apikey=key&method=gasoracle',
        # "polygon": "https://gasstation-mainnet.matic.network/",
        # "optimism": "10",
        # "arbitrum": "https://owlracle.info/arb/gas?apikey=877d078a2753422d8a6fbd3d092f5ddb",
        # "gnosis": "https://blockscout.com/xdai/mainnet/api/v1/gas-price-oracle",
        # "avalanche": "https://gavax.blockscan.com/gasapi.ashx?apikey=key&method=gasoracle",
        # "fantom": "https://owlracle.info/ftm/gas?apikey=877d078a2753422d8a6fbd3d092f5ddb"
    }

    chains = {
        "ethereum": '1',
        "binance": '56',
        "polygon": "137",
        # "optimism": "10",
        # "arbitrum": "42161",
        # "gnosis": "100",
        "avalanche": "43114",
        # "fantom": "250"
    }

    MODE = {
        "slow": [10, 20, 30, 40, 50],  # <1min
        "normal": [10, 30, 50, 70, 90],  # <30sec
        "fast": [50, 60, 70, 80, 90],  # <10sec
    }

    abi = json.loads(pkg_resources.read_text(__package__, 'erc20.json'))['result']

    def __init__(self, rpc_url, public_key, private_key, chain='ethereum'):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if chain == 'polygon' or chain == 'avalanche':
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        else:
            pass
        self.public_key = public_key
        self.private_key = private_key
        self.chain = chain
        self.chain_id = self.chains[chain]

    def estimate_gas_fees(self, speed="fast", nb_blocks=3):
        if speed not in self.MODE:
            raise ValueError("Invalid speed")

        # baseFee: Set by blockchain, varies at each block, always burned
        base_fee = self.w3.eth.get_block('pending').baseFeePerGas

        # next baseFee: Overestimation of baseFee in next block, difference always refunded
        next_base_fee = base_fee * 2

        # priorityFee: Set by user, tip/reward paid directly to miners, never returned
        reward_history = self.w3.eth.fee_history(
            nb_blocks, 'pending', self.MODE[speed])['reward']
        rewards = reduce(lambda x, y: x + y, reward_history)
        avg_reward = sum(rewards) // len(rewards)

        # Estimations: maxFee - (maxPriorityFee + baseFee actually paid) = Returned to used
        return {"maxPriorityFeePerGas": avg_reward,
                "maxFeePerGas": avg_reward + next_base_fee}

    def build_tx(self, raw_tx, speed='fast', nb_blocks=3):
        nonce = self.w3.eth.getTransactionCount(self.public_key)
        tx = raw_tx['tx']
        tx['nonce'] = nonce
        tx['to'] = self.w3.toChecksumAddress(tx['to'])
        tx['chainId'] = int(self.chain_id)
        tx['value'] = int(tx['value'])
        tx['gas'] = int(tx['gas'] * 1.25)
        if self.chain == 'ethereum' or self.chain == 'polygon' or self.chain == 'avalanche':
            gas = self.estimate_gas_fees(speed, nb_blocks)
            tx['maxPriorityFeePerGas'] = gas['maxPriorityFeePerGas']
            tx['maxFeePerGas'] = gas['maxFeePerGas']
            tx.pop('gasPrice')
        elif self.chain == 'binance':
            tx['gasPrice'] = int(tx['gasPrice'])
        else:
            print('Chain Unsupported at this time')
        return tx

    def sign_tx(self, tx):
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        return signed_tx

    def broadcast_tx(self, signed_tx, timeout=360):
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(tx_hash.hex())
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        return receipt, tx_hash.hex()

    def get_ERC20_balance(self, contract_address, decimal=None):
        contract = self.w3.eth.contract(address=self.w3.toChecksumAddress(contract_address), abi=self.abi)
        balance_in_wei = contract.functions.balanceOf(self.public_key).call()
        if decimal is None:
            return self.w3.fromWei(balance_in_wei, 'ether')
        else:
            return balance_in_wei / 10 ** decimal


if __name__ == '__main__':
    pass
