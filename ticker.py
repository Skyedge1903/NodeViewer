# utilities library
import serial
import time
import requests
import re
import json
import threading

# library to detect the operating system
import platform

# if we are on Windows
if platform.system() == "Windows":
    port_ = "COM"
# otherwise we are on linux
else:
    port_ = "/dev/ttyUSB"

address = "0x6cfa4a52a6718a0b721f5816bef04f9c3ce36c45"  # 0x6cfa4a52a6718a0b721f5816bef04f9c3ce36c45
address = address[2:]
include_address = (address != "")
if not include_address:
    address = "d8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

node = "412204"  # 412204
include_node = (node != "")

passive_token = "stETH"  # stETH
passive_token_income = 0.054
include_passive_token = (passive_token != "") and include_address

pages = '1' if include_address else '0'
pages += '1' if include_node else '0'
pages += '1' if include_passive_token or include_node else '0'


# function how to clean the return of the serial port
def cleanSerial(ser):
    rep = ser.readline().decode('utf-8').rstrip()
    print()
    print(rep)


# function how to clean the return of the serial port
def cleanSerialReturn(ser):
    return ser.readline().decode('utf-8').rstrip()


# function how create a tram to send to the serial port
def sendTram(ser, tram):
    while True:
        # we send the data frame
        for char in tram:
            ser.write(char.encode())
            time.sleep(0.002)
        time.sleep(0.2)
        note = cleanSerialReturn(ser)
        if note == tram.replace("#", ""):
            ser.write('1'.encode())
            print(tram.replace("#", ""))
            break
        else:
            ser.write('0'.encode())
            time.sleep(0.2)


def init():
    port_serie = True
    for i in range(0, 20):
        try:
            port_serie = serial.Serial(port=port_ + str(i), baudrate=9600)
            # print("serial port: " + port_ + str(i))
            # if the serial port does not return anything within 5 seconds, an error is returned,
            # open another process to count the time
            t = threading.Thread(target=cleanSerial, args=(port_serie,))
            t.start()
            t.join(5)
            if t.is_alive():
                # an error is returned
                raise Exception("connection error")

        except Exception:
            time.sleep(0.1)
            if i == 19:
                port_serie = False
        else:
            print("Find on : " + port_ + str(i))
            break

    if port_serie:
        cleanSerial(port_serie)
        sendTram(port_serie, "OK")
        sendTram(port_serie, pages)
        return port_serie
    else:
        return None


# function that replaces according to a correspondence table
def replace(text, correspondence):
    for key in correspondence:
        text = text.replace(key, correspondence[key])
    return text


def createType1():
    node_value = 0.0
    if include_node:
        page = get_page("https://beaconcha.in/validator/" + node)
        balance = re.search(r'<span .*>[0-9]+.[0-9][0-9][0-9][0-9][0-9] ETH</span>', page).group(0)
        balance = re.search(r'[0-9]+\.[0-9][0-9][0-9][0-9][0-9]', balance).group(0)
        node_value = balance
    page = get_page("https://etherchain.org/account/" + address + "#overview")
    values = list(re.finditer(r'[A-Za-z :]*\$[0-9,]+.[0-9]+', page))
    # we get the list of matches
    values = [x.group(0) for x in values]
    eth_price = values[1]
    for i in reversed(range(len(values))):
        if " " in values[i]:
            values.pop(i)
    # we keep only the 4 largest values
    eth = values.pop(0)

    tokens = list(re.finditer(r'<a href="/token/0x[A-Za-z0-9]+">[A-Za-z]+</a></td>', page))
    tokens = [x.group(0) for x in tokens]
    # only the name of the token between > and < is retrieved.
    tokens = [re.search(r'>[A-Za-z]+<', x).group(0) for x in tokens]
    # we remove the > and <
    tokens = [replace(x, {">": "", "<": ""}) for x in tokens]
    if include_node:
        # tokens are sorted according to their value
        tokens = sorted(tokens, key=lambda x: float(replace(values[tokens.index(x)], {"$": "", ",": ""})),
                        reverse=True)[:3]
        values = sorted(values, key=lambda x: float(replace(x, {"$": "", ",": ""})), reverse=True)[:3]

    else:
        # tokens are sorted according to their value
        tokens = sorted(tokens, key=lambda x: float(replace(values[tokens.index(x)], {"$": "", ",": ""})),
                        reverse=True)[:4]
        values = sorted(values, key=lambda x: float(replace(x, {"$": "", ",": ""})), reverse=True)[:4]
    # we put back in string
    values = [str(x) for x in values]
    values.insert(0, eth)
    tokens.insert(0, "ETH")
    if include_node:
        tokens.append("NODE")
        values.append(str(float(node_value) * float(replace(eth_price, {"$": "", ",": "", " ": ""}))))

    total = sum([float(replace(x, {"$": "", ",": ""})) for x in values])
    element = len(tokens)
    lbl = tokens
    # we transform the values into int to send them to the display
    chi = [int(float(replace(x, {"$": "", ",": ""})) * 360 / total) for x in values]

    # adds a space every 3 digits
    total = int(total)
    total = "{:,}".format(int(total)).replace(",", " ") + " USDC"
    total = (" " * (19 - len(total))) + total + "_"
    element = str(element) + "_"
    lbl = "_".join(lbl) + "_"
    chi = "_".join([str(x) for x in chi]) + "_#"
    return "1" + total + element + lbl + chi


def createType2():
    page = get_page("https://beaconcha.in/validator/" + node)
    validator = node
    rank1 = re.search(r'Rank [0-9]+\.*[0-9]* %', page).group(0)
    rank2 = re.search(r'<span id="validatorRank" .*>[0-9]+</span>', page).group(0)
    rank2 = rank2.replace(re.search(r'[0-9]+', rank2).group(0) + "px", "")
    rank2 = re.search(r'[0-9]+', rank2).group(0)
    status1 = re.search(r'<b>[A-Za-z]+</b> <i class="fas fa-power-off fa-sm text-success"></i>', page).group(0)
    status1 = "Active" if "Active" in status1 else "Inactive"
    efficiency = re.search(r'[0-9]+% - [A-Za-z]+', page).group(0)
    status2 = 1 if status1 == "Active" else 0
    balance = re.search(r'<span .*>[0-9]+.[0-9][0-9][0-9][0-9][0-9] ETH</span>', page).group(0)
    balance = re.search(r'[0-9]+\.[0-9][0-9][0-9][0-9][0-9]', balance).group(0)
    validator = "Validator " + str(validator) + "_"
    rank1 = str(rank1)
    rank1 = rank1 + (" " * (17 - len(rank1))) + "Balance" + "_"
    rank2 = str(rank2) + (" " * (24 - (len(str(rank2)) + len(str(balance))))) + str(balance) + "_"
    status1 = status1 + (" " * (24 - (len(str(status1)) + len(str(efficiency))))) + efficiency + "_"
    status2 = str(status2) + "_#"

    return "2" + validator + rank1 + rank2 + "Status     Effectiveness_" + status1 + status2


def createType3():
    steth = 0.0
    if include_passive_token:
        page = get_page("https://etherchain.org/account/" + address + "#overview")
        values = list(re.finditer(r'[A-Za-z :]*\$[0-9,]+.[0-9]+', page))
        # we get the list of matches
        values = [x.group(0) for x in values]
        for i in reversed(range(len(values))):
            if " " in values[i]:
                values.pop(i)

        tokens = list(re.finditer(r'<a href="/token/0x[A-Za-z0-9]+">[A-Za-z]+</a></td>', page))
        tokens = [x.group(0) for x in tokens]
        # only the name of the token between > and < is retrieved.
        tokens = [re.search(r'>[A-Za-z]+<', x).group(0) for x in tokens]
        # we remove the > and <
        tokens = [replace(x, {">": "", "<": ""}) for x in tokens]
        tokens.insert(0, "ETH")
        steth = 0
        for i in range(len(tokens)):
            if tokens[i] == "stETH":
                steth = (float(replace(values[i], {"$": "", ",": ""})) * passive_token_income) / 365
                break
    incomes = ["0.0", "0.0", "0.0"]
    page = get_page("https://etherchain.org/account/" + address + "#overview")
    values = list(re.finditer(r'[A-Za-z :]*\$[0-9,]+.[0-9]+', page))
    # we get the list of matches
    values = [x.group(0) for x in values]
    eth_price = values[1]
    if include_node:
        page = get_page("https://beaconcha.in/validator/" + node)
        incomes = list(re.finditer(r'\+[0-9,]+\.[0-9]+ ETH', page))
        incomes = [x.group(0) for x in incomes]

    eth_price = float(replace(eth_price, {"$": "", ",": "", " ": ""}))
    for i in range(len(incomes)):
        incomes[i] = float(replace(incomes[i], {"+": "", "ETH": "", " ": ""}))

    day_eth = incomes[0] + (steth / eth_price)
    day_eth = "+" + str(day_eth).split(".")[0] + '.' + str(day_eth).split(".")[1][:5] + " ETH"

    day_usdc = incomes[0] * eth_price
    day_usdc += steth

    month_eth = incomes[2] + ((steth * 30) / eth_price)
    month_eth = "+" + str(month_eth).split(".")[0] + '.' + str(month_eth).split(".")[1][:5] + " ETH"

    month_usdc = incomes[2] * eth_price
    month_usdc += steth * 30

    tab_income = [0 for _ in range(28)]
    if include_node:
        page = get_page("https://beaconcha.in/api/v1/validator/stats/" + node)
        page = json.loads(page)
        data = page["data"]
        # we only keep the last 28 days
        data = data[:28]
        variation = [x["end_balance"] - x["start_balance"] for x in reversed(data)]
        max_ = max(variation)
        amplification_factor = 10
        tab_income = [int((x / max_) * 70 * amplification_factor) - 70 * (amplification_factor - 1) for x in variation]
        # if there are negative values, we transform them into 0.
        tab_income = [0 if x < 0 else x for x in tab_income]

    day_eth = " " * (21 - len(day_eth)) + day_eth + "_"
    day_usdc = "+" + str(day_usdc).split('.')[0] + '.' + str(day_usdc).split('.')[1][:2] + " USDC"
    day_usdc = " " * (24 - len(day_usdc)) + day_usdc + "_"
    month_eth = " " * (19 - len(month_eth)) + month_eth + "_"
    month_usdc = "+" + str(month_usdc).split('.')[0] + '.' + str(month_usdc).split('.')[1][:2] + " USDC"
    month_usdc = " " * (24 - len(month_usdc)) + month_usdc + "_"
    tab_income = "_".join([str(x) for x in tab_income]) + "_#"

    return "3" + day_eth + day_usdc + month_eth + month_usdc + tab_income


# function that retrieves the content of a web page
def get_page(url):
    # we get the content of the page
    page = requests.get(url).text
    # we return the content
    return page


if __name__ == '__main__':

    port = init()
    if not port:
        print("Error: no port found.")
        exit()

    if pages[0] == "1":
        sendTram(port, createType1())
    if pages[1] == "1":
        sendTram(port, createType2())
    if pages[2] == "1":
        sendTram(port, createType3())

    cleanSerialReturn(port)

    while True:
        p = cleanSerialReturn(port)
        time.sleep(1)
        if p == "Page 1":
            sendTram(port, createType1())
        elif p == "Page 2":
            sendTram(port, createType2())
        elif p == "Page 3":
            sendTram(port, createType3())
