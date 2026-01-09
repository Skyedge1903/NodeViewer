import platform
import serial
import time
import threading
import json
from data import EthereumDataFetcher


class SerialDisplay:
    """Manages serial communication with a display device for showing Ethereum data."""

    def __init__(self, config_file="configure_me.json", pages="111"):
        with open(config_file, 'r') as f:
            config = json.load(f)['informations']
            self.address = config['address']
            self.staking_apr = config['staking_apr']
            self.assets = config['assets']

        self.fetcher = EthereumDataFetcher(self.address, self.staking_apr, self.assets)
        self.pages = pages
        self.ser = self._init_serial()
        if not self.ser:
            raise ValueError("No serial port found.")

        self._send_tram("OK")
        self._send_tram(self.pages)

    def _init_serial(self):
        """Initializes the serial connection by trying ports."""
        port_base = "COM" if platform.system() == "Windows" else "/dev/ttyUSB"
        for i in range(20):
            try:
                ser = serial.Serial(f"{port_base}{i}", 9600)
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
        """Reads and prints a line from the serial port."""
        ser = ser or self.ser
        print(ser.readline().decode('utf-8').rstrip())

    def _clean_serial_return(self):
        """Reads a line from the serial port without printing."""
        return self.ser.readline().decode('utf-8').rstrip()

    def _send_tram(self, tram):
        """Sends a data frame over serial with retry on failure."""
        while True:
            for char in tram:
                self.ser.write(char.encode())
                time.sleep(0.002)
            time.sleep(0.2)
            note = self._clean_serial_return()
            if note == tram.replace("#", ""):
                self.ser.write(b'1')
                print(note)
                break
            self.ser.write(b'0')
            time.sleep(0.2)

    def format_page1(self):
        """Formats data for page 1: Wallet overview pie chart."""
        wallet_info = self.fetcher.get_wallet_info()
        total_value = sum(float(i[1]) * float(i[2]) for i in wallet_info)
        labels = [i[0] for i in wallet_info]
        angles = [round((float(i[1]) * float(i[2]) / total_value) * 360, 2) for i in wallet_info]
        total_str = f"{int(total_value):,}".replace(",", " ") + " USDC"
        return f"1{total_str: >19}_{len(wallet_info)}_{"_".join(labels)}_{"_".join(map(str, angles))}_#"

    def format_page2(self):
        """Formats data for page 2: Node rank and stats."""
        stats = self.fetcher.get_node_rank()
        validator_count = self.fetcher.get_total_node()
        validator = f"Validator {stats[0][1]}_"
        rank_pct = f"Rank {int((stats[1][1] / validator_count) * 1000) / 10}%"
        rank_str = f"{rank_pct: <17}Balance_"
        rank_len = len(str(stats[1][1])) + len(str(stats[2][1]))
        rank_balance = f"{stats[1][1]}{' ' * (24 - rank_len)}{stats[2][1]}_"
        status_len = len(str(stats[3][1])) + len(stats[4][1])
        status_eff = f"{stats[3][1]}{' ' * (24 - status_len)}{stats[4][1]}_"
        status_code = f"{1 if stats[3][1] == 'Active' else 0}_#"
        return "2" + validator + rank_str + rank_balance + "Status     Effectiveness_" + status_eff + status_code

    def format_page3(self):
        """Formats data for page 3: Returns and income chart."""
        apr = self.fetcher.get_steth_return()

        def format_value(value, is_eth=False, sign="+"):
            nb = len(str(int(value)))
            rounded = round(value, 6 - nb)
            unit = " ETH" if is_eth else " USDC"
            return f"{sign}{rounded}{unit}"

        day_eth = format_value(apr[0][1], True)
        day_usdc = format_value(apr[0][2])
        month_eth = format_value(apr[1][1], True)
        month_usdc = format_value(apr[1][2])

        barres = self.fetcher.get_node_list_all()
        variation = list(map(float, barres))
        max_val = max(variation)
        tab_income = [max(0, int(x / max_val * 70)) for x in variation]

        return f"3{day_eth: >21}_{day_usdc: >24}_{month_eth: >19}_{month_usdc: >24}_{"_".join(map(str, tab_income))}_#"

    def run(self):
        """Runs the main loop to handle page requests over serial."""
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
    SerialDisplay().run()