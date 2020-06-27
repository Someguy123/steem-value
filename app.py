#!/usr/bin/env python3
import asyncio
import os
import logging
import nest_asyncio
from flask import Flask, jsonify, render_template
from datetime import datetime, timedelta
from privex.helpers import DictObject, env_int, env_cast
# from exchanges import get_target_value
# from exceptions import PairNotFound
from decimal import Decimal, ROUND_DOWN, getcontext
from threading import Thread, Lock
# from time import sleep
from privex.exchange import ExchangeManager
from privex.loghelper import LogHelper
from privex.helpers.cache import AsyncMemoryCache, adapter_set
from dotenv import load_dotenv
from os import getenv as env


load_dotenv()
nest_asyncio.apply()

CACHE_TIMEOUT = env_int('CACHE_TIMEOUT', 300)
LOOP_SLEEP = env_cast('LOOP_SLEEP', float, 60.0)

LogHelper(level=logging.ERROR, handler_level=logging.ERROR)
_lh = LogHelper('steemvalue')
h = _lh.add_console_handler()

# LogHelper('privex.exchange', handler_level=logging.DEBUG, clear_handlers=False)

logging.basicConfig()

log = _lh.get_logger()
log.propagate = False
# log = logging.getLogger()

adapter_set(AsyncMemoryCache())

app = Flask(__name__)

getcontext().prec = 40

#
# SteemValue
# Build by Someguy123
# Released under GNU AGPL Licence
#

STORE = DictObject(
    last_update=None, exchange_data=DictObject()
)

currencies = {
    'btc': 'Bitcoin',
    'bch': 'Bitcoin Cash (BCH)',
    'bsv': 'Bitcoin SV (BSV)',
    'bts': 'Bitshares (BTS)',
    'eth': 'Ethereum (ETH)',
    'eos': 'EOS (eosio.token)',
    'hbd': 'Hive Dollars (HBD)',
    'hive': 'HIVE',
    'ltc': 'Litecoin (LTC)',
    'xmr': 'Monero (XMR)',
    'sbd': 'Steem Dollars (SBD)',
    'steem': 'STEEM',
    'sys': 'SysCoin (SYS)',
    'tlos': 'Telos (TLOS)',
    'xzc': 'ZCoin (XZC)',
    'usd': 'US Dollar (USD)',
    'gbp': 'Great British Pound (GBP)',
    'eur': 'Euros (EUR)',
    'cad': 'Canadian Dollars (CAD)',
}

currency_list = [[k, v] for k, v in currencies.items()]

loop = asyncio.get_event_loop()

exm = ExchangeManager()
exchange_lock = asyncio.Lock()

if 'EUR' not in exm.proxy_coins: exm.proxy_coins.append('EUR')
if 'GBP' not in exm.proxy_coins: exm.proxy_coins.append('GBP')


async def _get_exchange_data(expire_check=True):
    if STORE.last_update is not None and len(STORE.exchange_data) > 0:
        expire_date = STORE.last_update + timedelta(seconds=CACHE_TIMEOUT)
        # not expired
        if expire_check and expire_date > datetime.utcnow():
            print('Getting cached data')
            return STORE.exchange_data
    print('Cache not found or expired. Querying exchanges.')
    # iterate over the currencies, and build matching pairs for every other
    # prevents any overlap/duplication, and allows fast currency adding
    for c in currencies:
        for p in currencies:
            if c == p: continue
            pair = '{}_{}'.format(c, p)
            rpair = '{}_{}'.format(p, c)
            # if there's a reversed pair, then we should
            # just skip this. If we're updating, that pair 
            # can do it's own thing
            if rpair in STORE.exchange_data: continue
            try:
                tv = await exm.get_pair(c, p)
                log.info('target value for %s_%s is: %f', c, p, tv)
                tvr = tv.quantize(Decimal('.000001'), rounding=ROUND_DOWN)
                STORE.exchange_data[pair] = str(tvr)
            except Exception as e:
                log.exception('ERROR: %s %s %s', p, type(e), str(e))
                continue
    
    STORE.last_update = datetime.utcnow()
    return STORE.exchange_data


async def get_exchange_data(expire_check=True):
    async with exchange_lock:
        retval = await _get_exchange_data(expire_check=expire_check)
    return retval


async def ex_loop_async():
    try:
        log.warning("ex_loop_async: getting exchange data")
        await get_exchange_data()
        log.warning("ex_loop_async: waiting %d seconds before re-running", LOOP_SLEEP)
        await asyncio.sleep(LOOP_SLEEP)
    except KeyboardInterrupt:
        return
    log.warning("ex_loop_async: re-running loop.")
    return await ex_loop_async()


def ex_loop():
    log.warning("ex_loop started")
    loop.run_until_complete(ex_loop_async())
    log.warning("ex_loop finished...")


# Start background thread to regularly update exchange rates
Thread(target=ex_loop).start()


@app.route('/')
def index():
    return render_template(
        'index.html', exdata=STORE.exchange_data, currencies=currency_list, currency_map=currencies,
        last_update=str(STORE.last_update).split('.')[0] + ' UTC-0'
    )


@app.route('/exdata.json')
def exchangedata():
    asyncio.run(get_exchange_data())
    return jsonify(STORE.exchange_data)


if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', False), port=int(os.environ.get('PORT', 5000)))
