import requests
import json
import re


# this function returns a list of tuples (crypto_name, amount, price)
def get_wallet_info(wallet_address):
    url = "https://api.ethplorer.io/getAddressInfo/{}?apiKey=freekey".format(wallet_address)
    response = requests.get(url)
    data = json.loads(response.text)
    if data['ETH']['balance'] != 0:
        result = [('ETH', data['ETH']['balance'], data['ETH']['price']['rate'])]
    else:
        result = []
    for token in data['tokens']:
        if token['tokenInfo']['price']:
            if token['tokenInfo']['symbol'] == 'STETH':
                bal = token['balance'] / 1000000000000000000
                result.append((token['tokenInfo']['symbol'], bal, token['tokenInfo']['price']['rate']))
            elif token['tokenInfo']['symbol'] == 'USDC':
                bal = token['balance'] / 1000000
                result.append((token['tokenInfo']['symbol'], bal, token['tokenInfo']['price']['rate']))
            elif token['tokenInfo']['symbol'] == 'PAXG':
                bal = token['balance'] / 1000000000000000000
                result.append((token['tokenInfo']['symbol'], bal, token['tokenInfo']['price']['rate']))
            else:
                result.append((token['tokenInfo']['symbol'], token['balance'], token['tokenInfo']['price']['rate']))
    # check if the wallet is linked to nodes and add sum of the nodes
    node_list = get_node(wallet_address)
    if len(node_list) != 0:
        node_info = []
        for node in node_list:
            node_info += get_node_info(node)
        for i in node_info:
            if i[0] in [j[0] for j in result]:
                index = [j[0] for j in result].index(i[0])
                result[index] = (result[index][0], result[index][1] + i[1], result[index][2])
            else:
                # add in first position
                result.insert(0, i)
    return result


# this function return a tuple (crypto_in_node, crypto_value_in_node)
def get_node_info(node_adresse):
    # get info of the node from the api beaconcha.in
    url = "https://beaconcha.in/api/v1/validator/{}".format(node_adresse)
    response = requests.get(url)
    data = json.loads(response.text)
    # get the eth value in usd
    url = "https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=ETH,USD"
    response = requests.get(url)
    eth_price = json.loads(response.text)['USD']
    return [("NODE", data['data']['balance'] / 1000000000, eth_price)]


# get 28 last days profits of the node day by day
def get_node_list(node_adresse):
    url = "https://beaconcha.in/api/v1/validator/stats/{}".format(node_adresse)
    response = requests.get(url)
    data = json.loads(response.text)
    # get data (day, end_balance - start_balance)
    result = []
    for day in data['data']:
        result.append((day['end_balance'] - day['start_balance']) / 1000000000)
    # we keep the last day first
    result = result[:28]
    # reverse the list to have the last day first
    result.reverse()
    return result


# get the nodes linked to the wallet
def get_node(wallet_address):
    url = "https://beaconcha.in/api/v1/validator/eth1/{}".format(wallet_address)
    response = requests.get(url)
    data = json.loads(response.text)
    return [i['validatorindex'] for i in data['data']]


# get the 28 last days cumulated profits of all nodes linked to the wallet
def get_node_list_all(wallet_address):
    node_list = get_node(wallet_address)
    result = []
    for node in node_list:
        node_info = get_node_list(node)
        if len(result) == 0:
            result = node_info
        else:
            for i in range(len(result)):
                result[i] += node_info[i]
    return result


# get the lido apr for STETH
def get_steth_return(wallet_address):
    wallet = get_wallet_info(wallet_address)
    # si il n'y a pas de steth ni de node on retourne 0
    if len([i for i in wallet if i[0] in ['STETH', 'NODE']]) == 0:
        return [('DAY', 0, 0), ('MONTH', 0, 0)]
    url = "https://lido.fi/"
    response = requests.get(url)
    data = response.text
    # the data-testid="ethereum-card" div
    data = re.findall(r'<div data-testid="ethereum-card".*?</div>', data, re.DOTALL)[0]
    # get 4.9% [0-9]+.[0-9]+%
    apr = float(re.findall(r'([0-9]+.[0-9]+)%', data)[0])
    day_return = (1 + apr / 100) ** (1 / 365) - 1
    month_return = (1 + apr / 100) ** (1 / 12) - 1
    # we get the day return for steth and NODE
    day_return_total_in_eth = sum([i[1] * day_return for i in wallet if i[0] in ['STETH', 'NODE']])
    # get the eth price from steth or node
    day_return_total_in_usd = day_return_total_in_eth * float([i[2] for i in wallet if i[0] in ['STETH', 'NODE']][0])
    month_return_total_in_eth = sum([i[1] * month_return for i in wallet if i[0] in ['STETH', 'NODE']])
    month_return_total_in_usd = month_return_total_in_eth * float(
        [i[2] for i in wallet if i[0] in ['STETH', 'NODE']][0])
    return [('DAY', day_return_total_in_eth, day_return_total_in_usd),
            ('MONTH', month_return_total_in_eth, month_return_total_in_usd)]


# get the rank, the balance, the status and effectiveness of the node
def get_node_rank(wallet_address):
    node_adresse = get_node(wallet_address)
    if len(node_adresse) == 0:
        return [('VALIDATOR', 'No node'), ('RANK', 'No node'), ('BALANCE', 'No node'), ('STATUS', 'No node'),
                ('EFFECTIVENESS', 'No node')]
    node_adresse = node_adresse[0]
    url = "https://beaconcha.in/api/v1/validator/{}/performance".format(node_adresse)
    response = requests.get(url)
    data = json.loads(response.text)
    url = "https://beaconcha.in/api/v1/validator/{}/attestationefficiency".format(node_adresse)
    response = requests.get(url)
    data2 = json.loads(response.text)
    data2 = data2['data'][0]['attestation_efficiency'] * 100
    data2 = data2 if data2 < 100 else 100
    data2 = str(round(data2, 2)) + '% - Perfect' if data2 > 99 else '% - Good' if data2 > 95 else '% - Bad'
    return [('VALIDATOR', node_adresse),
            ('RANK', data['data'][0]['rank7d']),
            ('BALANCE', data['data'][0]['balance'] / 1000000000),
            ('STATUS', 'Active' if data['status'] == 'OK' else 'Inactive'),
            ('EFFECTIVENESS', data2)]


# get the total number of ethereum nodes
def get_total_node():
    url = "https://beaconcha.in/api/v1/epoch/latest"
    response = requests.get(url)
    data = json.loads(response.text)
    return data['data']['validatorscount']


'''
adress = '0x6cfa4a52a6718a0b721f5816bef04f9c3ce36c45'

# Page 1
wallet_info = get_wallet_info(adress)
print(wallet_info)
total_value = [('TOTAL', sum([float(i[1]) * float(i[2]) for i in wallet_info]))]
print(total_value)

# Page 2
stats = get_node_rank(adress)
print(stats)

# Page 3
apr = get_steth_return(adress)
print(apr)
barres = get_node_list_all(adress)
print(barres)
'''
