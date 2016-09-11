from flask import Flask, jsonify, render_template
import os
from datetime import datetime, timedelta
from exchanges import get_target_value
from decimal import Decimal, ROUND_DOWN
app = Flask(__name__)

#
# SteemValue
# Build by Someguy123
# Released under GNU AGPL Licence
#

last_update = datetime.utcnow()
exchange_data = {}

currencies = {
    'btc': 'Bitcoin',
    'sbd': 'Steem Dollars (SBD)',
    'steem': 'STEEM',
    'ltc': 'LTC',
    'usd': 'USD',
    'eur': 'EUR',
    'cny': 'Chinese Yuan (CNY)'
}

def get_exchange_data(expire_check=True):
    global exchange_data, last_update
    if expire_check and last_update > datetime.utcnow() - timedelta(minutes=5):
        return exchange_data
    gtv = lambda x,y: str(get_target_value(x,y).quantize(Decimal('.0001'), rounding=ROUND_DOWN))
    # iterate over the currencies, and build matching pairs for every other
    # prevents any overlap/duplication, and allows fast currency adding
    for c in currencies:
        for p in currencies:
            if c == p: continue
            pair = '{}_{}'.format(c,p)
            rpair = '{}_{}'.format(p,c)
            if pair in exchange_data or rpair in exchange_data: continue
            try:
                exchange_data[pair] = gtv(c,p)
            except Exception as e:
                print('ERROR: ', type(e), str(e))
                continue
    
    last_update = datetime.utcnow()
    
    return exchange_data
    
# initial query
get_exchange_data(False)

@app.route('/')
def index():
    get_exchange_data()
    return render_template('index.html', exdata=exchange_data, currencies=currencies)

@app.route('/exdata.json')
def exchangedata():
    get_exchange_data()
    return jsonify(exchange_data)

if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', False), port=int(os.environ.get('PORT', 5000)))
