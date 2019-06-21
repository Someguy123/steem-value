import requests
import json
from decimal import Decimal, getcontext
from adapters import CacheAdapter


getcontext().prec = 8


class HuobiAdapter(CacheAdapter):
    def _get_price(self, pair):
        p = pair.split('_')
        # Huobi uses USDT
        p[0] = 'usdt' if p[0] == 'usd' else p[0]
        p[1] = 'usdt' if p[1] == 'usd' else p[1]

        # Invert pairs because huobi is backwards...
        p[0], p[1] = p[1], p[0]
        # Flatten pairs like 'BTC_USD' to 'btcusd'
        p = ''.join(p).lower()

        ticker_url = 'https://api.huobi.pro/market/detail/merged?symbol={}' \
                     .format(p)
        
        r = self.s.get(ticker_url)
        j = r.json()
        if 'tick' in j and 'close' in j['tick']:
            return Decimal(j['tick']['close'])
        raise Exception('error reading ticker {} from huobi'.format(p))
