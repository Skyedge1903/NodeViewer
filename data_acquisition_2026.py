import requests

# ------------------- CONFIGURATION GLOBALE -------------------
VALIDATOR_INDEX = "412204"
TOTAL_VALIDATORS = 973124
APR_NODE_STETH = 2.6  # APR fixe pour NODE / stETH

# Actifs manuels
ASSETS = {
    'USDC': {'balance': 36000, 'price': 1},
    'STETH': {'balance': 2.6}  # prix sera récupéré dynamiquement
}


# ------------------- WALLET INFO -------------------
def get_wallet_info(wallet_address):
    """Retourne les actifs du wallet avec balances et prix USD"""
    url = f"https://api.ethplorer.io/getAddressInfo/{wallet_address}?apiKey=freekey"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []

    data = resp.json()
    result = [(symbol, info['balance'], info['price']) for symbol, info in ASSETS.items() if symbol == 'USDC']

    # ETH
    if data.get('ETH', {}).get('balance', 0) > 0 and data['ETH'].get('price'):
        result.append(('ETH', data['ETH']['balance'], data['ETH']['price']['rate']))

    # Tokens
    for token in data.get('tokens', []):
        info = token.get('tokenInfo', {})
        if info.get('price'):
            symbol = info['symbol']
            price = info['price']['rate']
            decimals = int(info.get('decimals', 18))
            bal = token['balance'] / (10 ** decimals)
            if symbol == 'STETH':
                bal = ASSETS['STETH']['balance']
            result.append((symbol, bal, price))

    # Ajout NODE
    node_info = get_node_info(VALIDATOR_INDEX)
    if node_info:
        result.insert(0, node_info[0])

    return result


# ------------------- NODE INFO -------------------
def get_node_info(node_address):
    """Retourne balance NODE et prix ETH"""
    url = f"https://beaconcha.in/api/v1/validator/{node_address}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []

    data = resp.json()['data']
    balance_eth = round(data['balance'] / 1e9, 6)
    eth_price = requests.get(
        "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    ).json().get('ethereum', {}).get('usd', 0.0)

    return [("NODE", balance_eth, eth_price)]


def get_node(wallet_address):
    return [VALIDATOR_INDEX]


def get_node_list(node_address):
    """Rendement quotidien fixe (~3% APR) sur 28 jours"""
    daily = (APR_NODE_STETH / 100) / 365
    return [daily] * 28


def get_node_list_all(wallet_address):
    return get_node_list(VALIDATOR_INDEX)


# ------------------- STAKING RETURN -------------------
def get_steth_return(wallet_address):
    wallet = get_wallet_info(wallet_address)
    staked = [i for i in wallet if i[0] in ['STETH', 'NODE']]
    if not staked:
        return [('DAY', 0, 0), ('MONTH', 0, 0)]

    apr = APR_NODE_STETH
    day_r = (1 + apr / 100) ** (1 / 365) - 1
    month_r = (1 + apr / 100) ** (1 / 12) - 1
    eth_price = staked[0][2]

    day_eth = sum(i[1] * day_r for i in staked)
    month_eth = sum(i[1] * month_r for i in staked)

    return [('DAY', day_eth, day_eth * eth_price),
            ('MONTH', month_eth, month_eth * eth_price)]


# ------------------- NODE RANK -------------------
def get_node_rank(wallet_address):
    node = VALIDATOR_INDEX
    url_val = f"https://beaconcha.in/api/v1/validator/{node}"

    resp_val = requests.get(url_val)

    val_data = resp_val.json()['data']
    balance = round(val_data['balance'] / 1e9, 6)
    status = 'Active' if val_data['status'] in ['active_online'] else 'Inactive'
    rank = 318211

    eff = 99.58
    eff_str = (f"{round(eff,2)}% - Perfect" if eff > 99 else
               f"{round(eff,2)}% - Good" if eff > 95 else
               f"{round(eff,2)}% - Bad")

    return [('VALIDATOR', node), ('RANK', rank), ('BALANCE', balance), ('STATUS', status), ('EFFECTIVENESS', eff_str)]


# ------------------- TOTAL VALIDATORS -------------------
def get_total_node():
    return TOTAL_VALIDATORS
