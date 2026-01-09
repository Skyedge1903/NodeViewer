import platform
import serial
import time
import threading
import json
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

class SerialDisplay:
    def __init__(self, config_file="configure_me.json", pages="111"):
        with open(config_file, 'r') as f:
            self.address = json.load(f)['informations']['address']

        self.fetcher = EthereumDataFetcher(self.address)
        self.pages = pages
        self.ser = self._init_serial()
        if not self.ser:
            raise ValueError("No serial port found.")

        self._send_tram("OK")
        self._send_tram(self.pages)

    def _init_serial(self):
        port_base = "COM" if platform.system() == "Windows" else "/dev/ttyUSB"
        for i in range(20):
            try:
                ser = serial.Serial(f"{port_base}{i}", baudrate=9600)
                t = threading.Thread(target=self._clean_serial, args=(ser,))
                t.start()
                t.join(5)
                if t.is_alive():
                    raise TimeoutError("Connection timeout.")
                print(f"Found on: {port_base}{i}")
                self._clean_serial(ser)
                return ser
            except Exception:
                time.sleep(0.1)
        return None

    def _clean_serial(self, ser=None):
        ser = ser or self.ser
        rep = ser.readline().decode('utf-8').rstrip()
        print(rep)

    def _clean_serial_return(self):
        return self.ser.readline().decode('utf-8').rstrip()

    def _send_tram(self, tram):
        while True:
            for char in tram:
                self.ser.write(char.encode())
                time.sleep(0.002)
            time.sleep(0.2)
            note = self._clean_serial_return()
            if note == tram.replace("#", ""):
                self.ser.write(b'1')
                print(tram.replace("#", ""))
                break
            else:
                self.ser.write(b'0')
                time.sleep(0.2)

    def _replace(self, text, mapping):
        for key, value in mapping.items():
            text = text.replace(key, value)
        return text

    def format_page1(self):
        wallet_info = self.fetcher.get_wallet_info()
        total_value = sum(float(i[1]) * float(i[2]) for i in wallet_info)
        labels = [i[0] for i in wallet_info]
        angles = [round((float(i[1]) * float(i[2]) / total_value) * 360, 2) for i in wallet_info]

        total_str = f"{int(total_value):,}".replace(",", " ") + " USDC"
        total_padded = f"{total_str: >19}_"
        element_count = f"{len(wallet_info)}_"
        labels_joined = "_".join(labels) + "_"
        angles_joined = "_".join(map(str, angles)) + "_#"

        return "1" + total_padded + element_count + labels_joined + angles_joined

    def format_page2(self):
        stats = self.fetcher.get_node_rank()
        validator_count = self.fetcher.get_total_node()

        validator = f"Validator {stats[0][1]}_"
        rank_pct = f"Rank {int((stats[1][1] / validator_count) * 1000) / 10}%"
        rank_str = f"{rank_pct: <17}Balance_"
        rank_balance = f"{stats[1][1]}{' ' * (24 - (len(str(stats[1][1])) + len(str(stats[2][1]))))}{stats[2][1]}_"
        status_eff = f"{stats[3][1]}{' ' * (24 - (len(str(stats[3][1])) + len(stats[4][1])))}{stats[4][1]}_"
        status_code = f"{1 if stats[3][1] == 'Active' else 0}_#"

        return "2" + validator + rank_str + rank_balance + "Status     Effectiveness_" + status_eff + status_code

    def format_page3(self):
        apr = self.fetcher.get_steth_return()

        def format_value(value, is_eth=False, sign="+"):
            nb = len(str(int(value)))
            rounded = round(value, 6 - nb)
            unit = " ETH" if is_eth else " USDC"
            return f"{sign}{rounded}{unit}"

        day_eth = format_value(apr[0][1], is_eth=True)
        day_usdc = format_value(apr[0][2])
        month_eth = format_value(apr[1][1], is_eth=True)
        month_usdc = format_value(apr[1][2])

        day_eth_padded = f"{day_eth: >21}_"
        day_usdc_padded = f"{day_usdc: >24}_"
        month_eth_padded = f"{month_eth: >19}_"
        month_usdc_padded = f"{month_usdc: >24}_"

        barres = self.fetcher.get_node_list_all()
        variation = [float(i) for i in barres]
        max_val = max(variation)
        tab_income = [max(0, int((x / max_val) * 70)) for x in variation]  # Simplified
        tab_joined = "_".join(map(str, tab_income)) + "_#"

        return "3" + day_eth_padded + day_usdc_padded + month_eth_padded + month_usdc_padded + tab_joined

    def run(self):
        format_methods = {
            "Page 1": self.format_page1,
            "Page 2": self.format_page2,
            "Page 3": self.format_page3
        }

        for idx, enabled in enumerate(self.pages):
            if enabled == "1":
                self._send_tram(format_methods[f"Page {idx + 1}"]())

        self._clean_serial_return()

        while True:
            page = self._clean_serial_return()
            time.sleep(1)
            if page in format_methods:
                self._send_tram(format_methods[page]())


if __name__ == '__main__':
    display = SerialDisplay()
    display.run()