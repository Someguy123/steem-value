from flask import Flask, jsonify, render_template
import os
from datetime import datetime, timedelta
from exchanges import get_target_value
from exceptions import PairNotFound
from decimal import Decimal, ROUND_DOWN, getcontext
from threading import Thread, Lock
from time import sleep
import logging

logging.basicConfig()

log = logging.getLogger()

app = Flask(__name__)

getcontext().prec = 40

#
# SteemValue
# Build by Someguy123
# Released under GNU AGPL Licence
#

last_update = datetime.utcnow()
exchange_data = {}

currencies = {
    'btc': 'Bitcoin',
    'eos': 'EOS (eosio.token)',
    'sbd': 'Steem Dollars (SBD)',
    'steem': 'STEEM',
    'eth': 'Ethereum (ETH)',
    'ltc': 'Litecoin (LTC)',
    'usd': 'US Dollar (USD)',
    # 'eur': 'Euros (EUR)',
    #'golos': 'GOLOS (ГОЛОС)',
    #'gbg': 'Gold Backed GOLOS (GBG) (ЗОЛОТОЙ)',
    #'rur': 'Russian Rubles (RUB)',
    'xzc': 'ZCoin (XZC)',
    'sys': 'SysCoin (SYS)',    
}

def _get_exchange_data(expire_check=True):
    global exchange_data, last_update
    expire_date = last_update + timedelta(minutes=5)
    # not expired
    if expire_check and expire_date > datetime.utcnow():
        print('Getting cached data')
        return exchange_data
    print('Cache not found or expired. Querying exchanges.')
    gtv = lambda x,y: str(get_target_value(x,y).quantize(Decimal('.000001'), rounding=ROUND_DOWN))
    # iterate over the currencies, and build matching pairs for every other
    # prevents any overlap/duplication, and allows fast currency adding
    for c in currencies:
        for p in currencies:
            if c == p: continue
            pair = '{}_{}'.format(c,p)
            rpair = '{}_{}'.format(p,c)
            # if there's a reversed pair, then we should
            # just skip this. If we're updating, that pair 
            # can do it's own thing
            if rpair in exchange_data: continue
            try:
                # print('c is', c)
                # print('p is', p)
                # print('target value', repr(get_target_value(c,p)))
                # exchange_data[pair] = gtv(c,p)
                tv = get_target_value(c,p)
                log.warning('target value for %s_%s is: %f', c, p, tv)
                # if len(str(tv).split('.')[1]) < 6:
                    # tvr = tv.quantize(Decimal('.01'), rounding=ROUND_DOWN)                    
                # else:
                tvr = tv.quantize(Decimal('.000001'), rounding=ROUND_DOWN)
                # print('quantized target', tvr)
                exchange_data[pair] = str(tvr)
            except Exception as e:
                log.exception('ERROR: %s %s %s', p, type(e), str(e))
                continue
    
    last_update = datetime.utcnow()
    return exchange_data

get_exchange_lock = Lock()
def get_exchange_data(expire_check=True):
    global get_exchange_lock
    get_exchange_lock.acquire()
    retval = _get_exchange_data(expire_check=expire_check)
    get_exchange_lock.release()    
    return retval
    
def ex_loop():
    while True:
        get_exchange_data()
        sleep(200)

# initial query
get_exchange_data(False)
Thread(target=ex_loop).start()

@app.route('/')
def index():
    return render_template('index.html', exdata=exchange_data, currencies=currencies)

@app.route('/exdata.json')
def exchangedata():
    get_exchange_data()
    return jsonify(exchange_data)

if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', False), port=int(os.environ.get('PORT', 5000)))
