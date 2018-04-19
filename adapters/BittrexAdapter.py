import requests
import json
from decimal import Decimal, getcontext
from adapters import CacheAdapter


getcontext().prec = 8


class BittrexAdapter(CacheAdapter):
    """ Exchange adapter for Bittrex

    >>> b = BittrexAdapter()
    >>> b._get_price('btc_usd')
    123.00

    """
    def _get_price(self, pair):
        p = pair.split('_')
        pair = '{}-{}'.format(p[0], p[1])
        ticker_url = 'https://bittrex.com/api/v1.1/public/getticker?market=' + pair
        print(ticker_url)
        r = self.s.get(ticker_url)
        j = r.json()
        print('bittrex', j)
        if 'result' in j and 'Last' in j['result']:
            return Decimal(str(j['result']['Last']))
        raise Exception('error reading ticker data from bittrex')
