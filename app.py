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

def get_exchange_data(expire_check=True):
    global exchange_data, last_update
    if expire_check and last_update > datetime.utcnow():
        return exchange_data
    try:
        gtv = lambda x,y: str(get_target_value(x,y).quantize(Decimal('.0001'), rounding=ROUND_DOWN))
        exchange_data['sbd_btc'] = gtv('sbd','btc')
        exchange_data['steem_btc'] = gtv('steem','btc')
        exchange_data['sbd_usd'] = gtv('sbd','usd')
        exchange_data['steem_usd'] = gtv('steem','usd')
        exchange_data['sbd_eur'] = gtv('sbd','eur')
        exchange_data['steem_eur'] = gtv('steem','eur')
        exchange_data['steem_sbd'] = gtv('steem','sbd')
        exchange_data['btc_eur'] = gtv('btc','eur')
        exchange_data['btc_usd'] = gtv('btc','usd')
        exchange_data['eur_usd'] = gtv('eur','usd')
        last_update = datetime.utcnow()
    except e:
        print('ERROR: ', type(e), str(e))
        pass
    return exchange_data
    
# initial query
get_exchange_data(False)

@app.route('/')
def index():
    get_exchange_data()
    return render_template('index.html', exdata=exchange_data)

@app.route('/exdata.json')
def exchangedata():
    get_exchange_data()
    return jsonify(exchange_data)

if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', False))
