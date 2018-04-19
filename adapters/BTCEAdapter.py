import requests
import json
from decimal import Decimal, getcontext
from adapters import CacheAdapter


getcontext().prec = 8

# Unfortunately, BTC-E was shut down on the 29th of July 2017.
# This is here to copy for any exchanges which use the same API format (e.g. EXMO, YoBit)

class BTCEAdapter(CacheAdapter):
    """ Exchange adapter for BTC-e

    >>> b = BTCEAdapter()
    >>> b._get_price('btc_usd')
    123.00

    """
    def _get_price(self, pair):
        if pair.split('_')[1] not in ['usd', 'eur', 'gbp', 'rub']:
            # btc-e is backwards for altcoins, so flip the pair!
            pair_cut = list(pair.split('_'))
            pair = '{1}_{0}'.format(*pair_cut)
        ticker_url = 'https://wex.nz/api/2/{}/ticker'.format(pair)
        r = self.s.get(ticker_url)
        print(ticker_url)
        j = r.json()
        if 'ticker' in j and 'last' in j['ticker']:
            return Decimal(str(j['ticker']['last']))
        raise Exception('error reading ticker data from btc-e')
