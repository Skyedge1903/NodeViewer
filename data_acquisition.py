import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class EthereumDataFetcher:
    STAKING_APR = 0.026  # 2.6% annual fixed

    ASSETS = {
        'USDC': {'balance': 36000, 'price': 1},
        'STETH': {'balance': 2.6}
    }

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://beaconcha.in/",
        "Connection": "keep-alive",
    }

    def __init__(self, address):
        self.address = address
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        session.headers.update(self.DEFAULT_HEADERS)
        retries = Retry(
            total=5,
            backoff_factor=1.2,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _safe_get(self, url, expect_json=True):
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json() if expect_json else resp.text

    def get_wallet_info(self):
        url = f"https://api.ethplorer.io/getAddressInfo/{self.address}?apiKey=freekey"
        data = self._safe_get(url)
        result = [('USDC', self.ASSETS['USDC']['balance'], 1)]  # Manual USDC

        # ETH
        eth = data.get('ETH', {})
        if eth.get('balance', 0) > 0 and eth.get('price'):
            result.append(('ETH', eth['balance'], eth['price']['rate']))

        # Tokens
        for token in data.get('tokens', []):
            info = token.get('tokenInfo', {})
            if not info.get('price'):
                continue
            symbol = info.get('symbol')
            decimals = int(info.get('decimals', 18))
            balance = token['balance'] / (10 ** decimals)
            price = info['price']['rate']
            if symbol == 'STETH':
                balance = self.ASSETS['STETH']['balance']
            result.append((symbol, balance, price))

        # Node
        node = self.get_node()[0]
        node_info = self.get_node_info(node)
        if node_info:
            result.insert(0, node_info[0])

        return result

    def get_node_info(self, validator_index):
        data = self._safe_get(f"https://beaconcha.in/api/v1/validator/{validator_index}")
        eth_price = self._safe_get("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD")["USD"]
        balance_eth = data['data']['balance'] / 1e9
        return [("NODE", balance_eth, eth_price)]

    def get_node_list(self, validator_index):
        data = self._safe_get(f"https://beaconcha.in/api/v1/validator/stats/{validator_index}")
        profits = []
        for day in data['data'][:28]:
            try:
                profits.append((day['end_balance'] - day['start_balance']) / 1e9)
            except Exception:
                profits.append(0.00704)
        profits.reverse()
        return profits

    def get_node(self):
        data = self._safe_get(f"https://beaconcha.in/api/v1/validator/eth1/{self.address}")
        return [i['validatorindex'] for i in data['data']]

    def get_node_list_all(self):
        nodes = self.get_node()
        aggregated = []
        for node in nodes:
            daily = self.get_node_list(node)
            if not aggregated:
                aggregated = daily
            else:
                aggregated = [a + b for a, b in zip(aggregated, daily)]
        return aggregated

    def get_steth_return(self):
        wallet = self.get_wallet_info()
        staking_assets = [i for i in wallet if i[0] in ('STETH', 'NODE')]
        if not staking_assets:
            return [('DAY', 0, 0), ('MONTH', 0, 0)]

        day_rate = (1 + self.STAKING_APR) ** (1 / 365) - 1
        month_rate = (1 + self.STAKING_APR) ** (1 / 12) - 1

        total_eth = sum(balance for _, balance, _ in staking_assets)
        eth_price = staking_assets[0][2]

        day_eth = total_eth * day_rate
        month_eth = total_eth * month_rate

        return [
            ('DAY', day_eth, day_eth * eth_price),
            ('MONTH', month_eth, month_eth * eth_price)
        ]

    def get_node_rank(self):
        nodes = self.get_node()
        if not nodes:
            return [
                ('VALIDATOR', 'No node'),
                ('RANK', 'No node'),
                ('BALANCE', 'No node'),
                ('STATUS', 'No node'),
                ('EFFECTIVENESS', 'No node')
            ]

        validator = nodes[0]
        perf = self._safe_get(f"https://beaconcha.in/api/v1/validator/{validator}/performance")
        eff = self._safe_get(f"https://beaconcha.in/api/v1/validator/{validator}/attestationefficiency")

        efficiency = min(100, round(eff['data'][0]['attestation_efficiency'] * 100, 2))
        label = "Perfect" if efficiency > 99 else "Good" if efficiency > 95 else "Bad"

        return [
            ('VALIDATOR', validator),
            ('RANK', perf['data'][0]['rank7d']),
            ('BALANCE', perf['data'][0]['balance'] / 1e9),
            ('STATUS', 'Active' if perf['status'] == 'OK' else 'Inactive'),
            ('EFFECTIVENESS', f"{efficiency}% - {label}")
        ]

    def get_total_node(self):
        data = self._safe_get("https://beaconcha.in/api/v1/epoch/latest")
        return data['data']['validatorscount']

if __name__ == '__main__':

    '''
    address = '0x6cfa4a52a6718a0b721f5816bef04f9c3ce36c45'
    fetcher = EthereumDataFetcher(address)

    # Page 1
    wallet_info = fetcher.get_wallet_info()
    print(wallet_info)
    total_value = [('TOTAL', sum(float(i[1]) * float(i[2]) for i in wallet_info))]
    print(total_value)

    # Page 2
    stats = fetcher.get_node_rank()
    print(stats)

    # Page 3
    apr = fetcher.get_steth_return()
    print(apr)
    barres = fetcher.get_node_list_all()
    print(barres)
    '''