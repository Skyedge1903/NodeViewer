# library to detect the operating system
import platform
# utilities library
import serial
import time
import threading
import json
import data_acquisition as da

# if we are on Windows
if platform.system() == "Windows":
    port_ = "COM"
# otherwise we are on linux
else:
    port_ = "/dev/ttyUSB"

# open the config file
with open("configure_me.json", 'r') as json_file:
    address = json.load(json_file)['informations']['address']

pages = '111'


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
    wallet_info = da.get_wallet_info(address)
    total_value = [('TOTAL', sum([float(i[1]) * float(i[2]) for i in wallet_info]))]
    lbl = [i[0] for i in wallet_info]
    # nos chiffres sont trop grands on les rapoorte à 360°
    chi = [round((float(i[1]) * float(i[2])) / total_value[0][1] * 360, 2) for i in wallet_info]

    # adds a space every 3 digits
    total = "{:,}".format(int(total_value[0][1])).replace(",", " ") + " USDC"
    total = (" " * (19 - len(total))) + total + "_"
    element = str(len(wallet_info)) + "_"
    lbl = "_".join(lbl) + "_"
    chi = "_".join([str(x) for x in chi]) + "_#"
    return "1" + total + element + lbl + chi


def createType2():
    stats = da.get_node_rank(address)
    validator = stats[0][1]
    validator_count = da.get_total_node()
    rank1 = 'Rank ' + str(int((stats[1][1]/validator_count)*1000)/10) + "%"
    rank2 = stats[1][1]
    status1 = stats[3][1]
    efficiency = stats[4][1]
    status2 = 1 if status1 == "Active" else 0
    balance = stats[2][1]
    validator = "Validator " + str(validator) + "_"
    rank1 = str(rank1)
    rank1 = rank1 + (" " * (17 - len(rank1))) + "Balance" + "_"
    rank2 = str(rank2) + (" " * (24 - (len(str(rank2)) + len(str(balance))))) + str(balance) + "_"
    status1 = status1 + (" " * (24 - (len(str(status1)) + len(str(efficiency))))) + efficiency + "_"
    status2 = str(status2) + "_#"

    return "2" + validator + rank1 + rank2 + "Status     Effectiveness_" + status1 + status2


def createType3():
    apr = da.get_steth_return(address)

    day_eth = apr[0][1]
    # we count the number of digits before the decimal point
    nb = len(str(int(day_eth)))
    # we keep 6 - nb digits after the decimal point
    day_eth = '+' + str(round(day_eth, 6 - nb)) + " ETH"

    day_usdc = apr[0][2]
    nb = len(str(int(day_usdc)))
    day_usdc = str(round(day_usdc, 6 - nb)) + " USDC"

    month_eth = apr[1][1]
    nb = len(str(int(month_eth)))
    month_eth = '+' + str(round(month_eth, 6 - nb)) + " ETH"

    month_usdc = apr[1][2]
    nb = len(str(int(month_usdc)))
    month_usdc = str(round(month_usdc, 6 - nb)) + " USDC"

    barres = da.get_node_list_all(address)
    variation = [float(i) for i in barres]
    max_ = max(variation)
    amplification_factor = 1
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
