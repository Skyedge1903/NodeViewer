import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class EthereumDataFetcher:
    """Fetches Ethereum-related data from various APIs."""

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json,text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://beaconcha.in/",
        "Connection": "keep-alive",
    }

    def __init__(self, address, staking_apr, assets):
        self.address = address
        self.staking_apr = staking_apr
        self.assets = assets
        self.session = self._create_session()
        self._cache = {}

    def _create_session(self):
        """Creates a requests session with retry logic."""
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
        """Performs a safe GET request with error handling."""
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json() if expect_json else resp.text

    def get_wallet_info(self):
        """Retrieves wallet information including assets and node details."""
        if 'wallet_info' in self._cache:
            return self._cache['wallet_info']

        url = f"https://api.ethplorer.io/getAddressInfo/{self.address}?apiKey=freekey"
        data = self._safe_get(url)
        result = [('USDC', self.assets['USDC']['balance'], 1)]

        # Add ETH if present
        eth = data.get('ETH', {})
        if eth.get('balance', 0) > 0 and eth.get('price'):
            result.append(('ETH', eth['balance'], eth['price']['rate']))

        # Add tokens
        for token in data.get('tokens', []):
            info = token.get('tokenInfo', {})
            if not info.get('price'):
                continue
            symbol = info['symbol']
            decimals = int(info.get('decimals', 18))
            balance = token['balance'] / (10 ** decimals)
            price = info['price']['rate']
            if symbol == 'STETH':
                balance = self.assets['STETH']['balance']
            result.append((symbol, balance, price))

        # Add node info
        node = self.get_node()[0]
        node_info = self.get_node_info(node)
        if node_info:
            result.insert(0, node_info[0])

        self._cache['wallet_info'] = result
        return result

    def get_node_info(self, validator_index):
        """Gets information about a specific node."""
        data = self._safe_get(f"https://beaconcha.in/api/v1/validator/{validator_index}")
        eth_price = self._safe_get("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD")["USD"]
        balance_eth = data['data']['balance'] / 1e9
        return [("NODE", balance_eth, eth_price)]

    def get_node_list(self, validator_index):
        """Retrieves daily profits for a node over the last 28 days."""
        data = self._safe_get(f"https://beaconcha.in/api/v1/validator/stats/{validator_index}")
        profits = []
        for day in data['data'][:28]:
            if 'end_balance' in day and 'start_balance' in day:
                profits.append((day['end_balance'] - day['start_balance']) / 1e9)
            else:
                profits.append(0.00704)
        return profits[::-1]

    def get_node(self):
        """Fetches the list of node validator indices for the address."""
        if 'nodes' in self._cache:
            return self._cache['nodes']
        data = self._safe_get(f"https://beaconcha.in/api/v1/validator/eth1/{self.address}")
        nodes = [i['validatorindex'] for i in data['data']]
        self._cache['nodes'] = nodes
        return nodes

    def get_node_list_all(self):
        """Aggregates daily profits across all nodes."""
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
        """Calculates daily and monthly returns for staked assets."""
        wallet = self.get_wallet_info()
        staking_assets = [i for i in wallet if i[0] in ('STETH', 'NODE')]
        if not staking_assets:
            return [('DAY', 0, 0), ('MONTH', 0, 0)]

        day_rate = (1 + self.staking_apr) ** (1 / 365) - 1
        month_rate = (1 + self.staking_apr) ** (1 / 12) - 1
        total_eth = sum(b for _, b, _ in staking_assets)
        eth_price = staking_assets[0][2]
        day_eth = total_eth * day_rate
        month_eth = total_eth * month_rate
        return [
            ('DAY', day_eth, day_eth * eth_price),
            ('MONTH', month_eth, month_eth * eth_price)
        ]

    def get_node_rank(self):
        """Retrieves ranking and performance stats for the primary node."""
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
        validator_data = self._safe_get(f"https://beaconcha.in/api/v1/validator/{validator}")
        perf = self._safe_get(f"https://beaconcha.in/api/v1/validator/{validator}/performance")
        eff = self._safe_get(f"https://beaconcha.in/api/v1/validator/{validator}/attestationefficiency")
        status = validator_data['data']['status']
        is_active = status.startswith('active_online')
        efficiency = min(100, round(eff['data'][0]['attestation_efficiency'] * 100, 2))
        label = "Perfect" if efficiency > 99 else "Good" if efficiency > 95 else "Bad"
        return [
            ('VALIDATOR', validator),
            ('RANK', perf['data'][0]['rank7d']),
            ('BALANCE', perf['data'][0]['balance'] / 1e9),
            ('STATUS', 'Active' if is_active else 'Inactive'),
            ('EFFECTIVENESS', f"{efficiency}% - {label}")
        ]

    def get_total_node(self):
        """Gets the total number of validators in the network."""
        data = self._safe_get("https://beaconcha.in/api/v1/epoch/latest")
        return data['data']['validatorscount']