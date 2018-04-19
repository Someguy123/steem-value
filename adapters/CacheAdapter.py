import requests
import json
from decimal import Decimal, getcontext
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

class CacheAdapter(object):
    """ Base class which wraps `_get_price` with a cache layer

    Abstract class, not to be instantiated
    example usage:
    
    >>> class PoloniexAdapter(CacheAdapter):
    >>>    def _get_price(self, pair):
    >>>        return Decimal('1')
    >>> p = PoloniexAdapter()
    >>> p.get_pair('btc_usd')
    123.00
    
    """
    s = requests.session()
    # works similar to django's, modified for flask caching


    def get_or_set(self, key, func, serialize=None):
        c = cache.get(key)
        if c is None:
            data = func()
            # print('setting key: ', key, data)
            if serialize == 'object':
                dataser = json.dumps(data)
            if serialize == 'decimal':
                dataser = str(data)
            cache.set(key, dataser)
            return data
        if serialize == 'object':
            c = json.loads(c)
        if serialize == 'decimal':
            c = Decimal(str(c))
        return c
    def get_price(self, pair):
        self.pair = pair
        return self.get_or_set('price:' + pair, self._get_cache_price, 'decimal')

    def _get_cache_price(self):
        return self._get_price(self.pair)

    def _get_price(self, pair):
        raise NotImplemented('Please define _get_price in your adapter!')
