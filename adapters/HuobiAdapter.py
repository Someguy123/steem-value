import requests
import json
from decimal import Decimal, getcontext
from adapters import CacheAdapter


getcontext().prec = 8


class HuobiAdapter(CacheAdapter):
    def _get_price(self, pair):
        p = pair.split('_')
        if p[0] != 'cny':
            raise PairNotFound('Huobi only does CNY')
        
        ticker_url = 'https://api.huobi.com/staticmarket/ticker_{}_json.js' \
                     .format(p[1])
        
        r = self.s.get(ticker_url)
        print(ticker_url)
        j = r.json()
        if 'ticker' in j and 'last' in j['ticker']:
            return Decimal(str(j['ticker']['last']))
        raise Exception('error reading ticker data from huobi')
