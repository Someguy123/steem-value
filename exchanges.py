import requests
from decimal import Decimal, getcontext
import json
# from django.core.cache import cache

#
# Someguy123's Ultimate Python Exchange API
# Modified for Flask
# Released under the GNU AGPL
#


from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

# works similar to django's, modified for flask caching
def get_or_set(key, func, serialize=None):
    c = cache.get(key)
    if c is None:
        data = func()
        # print('setting key: ', key, data)
        if serialize == 'object': dataser = json.dumps(data)
        if serialize == 'decimal': dataser = str(data)
        cache.set(key, dataser)
        return data
    if serialize == 'object': c = json.loads(c)  
    if serialize == 'decimal': c = Decimal(str(c))
    return c

class CacheAdapter(object):
    s = requests.session()
    
    def get_price(self, pair):
        self.pair = pair
        return get_or_set('price:'+pair, self._get_cache_price, 'decimal')

    def _get_cache_price(self):
        return self._get_price(self.pair)

    def _get_price(self, pair):
        raise NotImplemented('Please define _get_price in your adapter!')


class PoloniexAdapter(CacheAdapter):
    def _get_price(self, pair):
        pair = self.pair
        pair = pair.upper()
        j = get_or_set('polodata', self.get_polo_data, 'object')
        # print('polo data', j)
        if pair in j and 'last' in j[pair]:
            return Decimal(str(j[pair]['last']))

        raise Exception('ticker error, or pair not found on exchange')
     
    def get_polo_data(self):
        r = self.s.get('https://poloniex.com/public?command=returnTicker')
        return r.json()
    


class BTCEAdapter(CacheAdapter):
    def _get_price(self, pair):
        if pair.split('_')[1] not in ['usd', 'eur', 'gbp', 'rub']:
            # btc-e is backwards for altcoins, so flip the pair!
            pair_cut = list(pair.split('_'))
            pair = '{1}_{0}'.format(*pair_cut)
        ticker_url = 'https://btc-e.com/api/2/{}/ticker'.format(pair)
        r = self.s.get(ticker_url)
        j = r.json()
        if 'ticker' in j and 'last' in j['ticker']:
            return Decimal(str(j['ticker']['last']))
        raise Exception('error reading ticker data from btc-e')

class HuobiAdapter(CacheAdapter):
    def _get_price(self, pair):
        p = pair.split('_')
        if p[0] != 'cny': raise PairNotFound('Huobi only does CNY')
        ticker_url = 'https://api.huobi.com/staticmarket/ticker_{}_json.js'.format(p[1])
        r = self.s.get(ticker_url)
        j = r.json()
        if 'ticker' in j and 'last' in j['ticker']:
            return Decimal(str(j['ticker']['last']))
        raise Exception('error reading ticker data from huobi')

class BittrexAdapter(CacheAdapter):
    def _get_price(self, pair):
        p = pair.split('_')
        pair = '{}-{}'.format(p[0], p[1])
        ticker_url = 'https://bittrex.com/api/v1.1/public/getticker?market='+pair;
        r = self.s.get(ticker_url)
        j = r.json()
        if 'result' in j and 'Last' in j['result']:
            return Decimal(str(j['result']['Last']))
        raise Exception('error reading ticker data from bittrex')

class LiquiAdapter(CacheAdapter):
    def _get_price(self, pair):
        # Liqui flips, e.g. btc_gbg = gbg_btc
        pair_cut = list(pair.split('_'))
        pair = '{1}_{0}'.format(*pair_cut)
        ticker_url = 'https://api.liqui.io/api/3/ticker/'+pair;
        r = self.s.get(ticker_url)
        j = r.json()
        if pair in j and 'last' in j[pair]:
            return Decimal(str(j[pair]['last']))
        raise Exception('error reading ticker data from liqui')

# avoid initializing an adapter more than once
ADAPTERS = {}

# which adapter can get us the price for a certain pair?
PAIRS = {
    'usd_btc': BTCEAdapter,
    'eur_btc': BTCEAdapter,
    'usd_ltc': BTCEAdapter,
    'btc_ltc': BTCEAdapter,
    'rur_btc': BTCEAdapter,
    'btc_eth': BTCEAdapter,
    'btc_sbd': BittrexAdapter,
    'btc_steem': BittrexAdapter,
    'cny_btc': HuobiAdapter,
    'btc_golos': BittrexAdapter,
    'btc_gbg': LiquiAdapter
}


def get_pair_value(pair, invert=False) -> Decimal:
    """
    Initializes an adapter and returns the last price
    Also handles inversion automatically
    :param pair: string, e.g. btc_usd
    :param invert: Invert the pair order and then invert the result price
    :return: Decimal value
    """
    pair = '{1}_{0}'.format(*pair.split('_')) if invert else pair
    if pair not in PAIRS:
        # first see if we can invert it
        if not invert:
            return get_pair_value(pair, invert=True)
        # if we already tried inverting, give up.
        raise PairNotFound('pair was not found')

    # initialize adapter if it isn't already
    adp_name = PAIRS[pair].__name__
    if adp_name not in ADAPTERS:
        ADAPTERS[adp_name] = PAIRS[pair]()

    adapter = ADAPTERS[adp_name]
    return Decimal('1') / adapter.get_price(pair) if invert else adapter.get_price(pair)


def get_target_value(coin, target='usd') -> Decimal:
    """
    Returns the target currency (i.e. USD) value for any coin, attempts to proxy via BTC if
    there's no direct USD pair.

    Example: (September 2016),
    >>> get_target_value('btc', 'usd')
        Decimal('620.449')

    If the target/coin is BTC, will probably return directly (direct hop).

    :param coin: Exchange label for a coin, e.g. btc, sbd, ltc
    :param target: Target currency, e.g. usd, eur, doge
    :raise PairNotFound:
    :return: Decimal USD value
    """
    # direct hop
    pair_target = '{}_{}'.format(target, coin)
    # reverse hop
    pair_flip = '{}_{}'.format(coin, target)
    # bitcoin hop
    pair_btc = '{}_{}'.format('btc', target)
    # target BTC value
    target_btc = '{}_{}'.format('btc', coin)

    # do we have a direct hop?
    if pair_target in PAIRS:
        return get_pair_value(pair_target)
    # do we have a reverse hop?
    if pair_flip in PAIRS:
        return Decimal(1) / get_pair_value(pair_flip)
    # no we don't. proxy it via BTC
    # get_pair_value THROWS PairNotFound exception
    # step 1, get pair price in BTC
    btc_price = get_pair_value(pair_btc)
    # step 2, times that by the target pair price
    btc_target_price = get_pair_value(target_btc)
    return (Decimal('1') / btc_price) * btc_target_price


class PairNotFound(BaseException):
    pass
