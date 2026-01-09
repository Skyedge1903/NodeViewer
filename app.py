from flask import Flask, render_template, jsonify
import json
from data import EthereumDataFetcher
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates')
server = app


with open('configure_me.json', 'r') as f:
    config = json.load(f)['informations']


def fetch_data():
    """Récupère toutes les données Ethereum"""
    fetcher = EthereumDataFetcher(
        config['address'],
        config['staking_apr'],
        config['assets']
    )

    wallet_info = fetcher.get_wallet_info()
    total_value = sum(float(i[1]) * float(i[2]) for i in wallet_info)
    total_str = f"{int(total_value):,} ".replace(",", " ") + " USDC"
    asset_labels = [i[0] for i in wallet_info]
    asset_values = [float(i[1]) * float(i[2]) for i in wallet_info]

    stats = fetcher.get_node_rank()
    total_nodes = fetcher.get_total_node()
    validator = stats[0][1]
    rank = stats[1][1]
    balance = stats[2][1]
    status = stats[3][1]
    effectiveness = stats[4][1]
    active = status == 'Active'
    rank_pct = round((rank / total_nodes) * 100, 1) if total_nodes > 0 else 0.0

    apr = fetcher.get_steth_return()
    day_eth, day_usdc = apr[0][1], apr[0][2]
    month_eth, month_usdc = apr[1][1], apr[1][2]

    def fmt_val(v, is_eth=True):
        nb = len(str(int(abs(v))))
        rounded = round(v, 6 - nb)
        unit = " ETH" if is_eth else " USDC"
        sign = "+" if v >= 0 else ""
        return f"{sign}{rounded}{unit}"

    day_eth_str = fmt_val(day_eth, True)
    day_usdc_str = fmt_val(day_usdc, False)
    month_eth_str = fmt_val(month_eth, True)
    month_usdc_str = fmt_val(month_usdc, False)

    barres = fetcher.get_node_list_all()
    variation = [float(x) for x in barres]
    max_val = max(variation) if variation else 1
    graph_heights = [max(0, int((x / max_val) * 100)) for x in variation]

    return {
        'total_str': total_str,
        'asset_labels': asset_labels,
        'asset_values': asset_values,
        'validator': validator,
        'rank_pct': rank_pct,
        'rank': rank,
        'balance': balance,
        'status': status,
        'effectiveness': effectiveness,
        'active': active,
        'day_eth_str': day_eth_str,
        'day_usdc_str': day_usdc_str,
        'month_eth_str': month_eth_str,
        'month_usdc_str': month_usdc_str,
        'graph_heights': graph_heights,
        'loaded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.route('/')
def loader():
    """Page de chargement qui apparaît immédiatement"""
    return render_template('loading.html')


@app.route('/fetch_data')
def fetch_data_api():
    """Endpoint pour récupérer les données JSON"""
    try:
        data = fetch_data()
        return jsonify({'ready': True, 'data': data})
    except Exception as e:
        return jsonify({'ready': False, 'error': str(e)})


@app.route('/dashboard')
def dashboard():
    """Affiche la page principale avec les données déjà prêtes"""
    return render_template('index.html', **fetch_data())


# Route pour favicon
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))
