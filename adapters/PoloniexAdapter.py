import requests
import json
from decimal import Decimal, getcontext
from adapters import CacheAdapter


getcontext().prec = 8


class PoloniexAdapter(CacheAdapter):
    ticker_url = 'https://poloniex.com/public?command=returnTicker'
    """ Exchange adapter for Poloniex

    >>> b = PoloniexAdapter()
    >>> b._get_price('btc_usd')
    123.00

    """
    def _get_price(self, pair):
        # pair = self.pair
        print(self.ticker_url)
        # Poloniex uses Tether USD, instead of a standard USD pair
        p = pair.split('_')
        p[0] = 'usdt' if p[0] == 'usd' else p[0]
        p[1] = 'usdt' if p[1] == 'usd' else p[1]
        pair = '_'.join(p)

        pair = pair.upper()
        # Poloniex returns ALL of their pairs in one big lump
        # so we cache the whole block, to avoid sending a request for every coin.

        j = self.get_or_set('polodata', self.get_polo_data, 'object')
        # print('polo data', j)
        if pair in j and 'last' in j[pair]:
            return Decimal(str(j[pair]['last']))

        raise Exception('ticker error, or pair not found on exchange')

    def get_polo_data(self):
        r = self.s.get(self.ticker_url)
        return r.json()
