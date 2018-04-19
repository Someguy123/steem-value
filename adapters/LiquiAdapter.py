from decimal import Decimal, getcontext
from adapters import CacheAdapter


getcontext().prec = 8


class LiquiAdapter(CacheAdapter):
    """ Exchange adapter for Liqui

    >>> b = LiquiAdapter()
    >>> b._get_price('btc_usd')
    123.00

    """
    def _get_price(self, pair):
        # Liqui flips, e.g. btc_gbg = gbg_btc
        pair_cut = list(pair.split('_'))
        pair = '{1}_{0}'.format(*pair_cut)
        ticker_url = 'https://api.liqui.io/api/3/ticker/' + pair
        r = self.s.get(ticker_url)
        j = r.json()
        print('liqui', j)
        if pair in j and 'last' in j[pair]:
            return Decimal(str(j[pair]['last']))
        raise Exception('error reading ticker data from liqui')
