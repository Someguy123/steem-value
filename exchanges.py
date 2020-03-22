import requests
from decimal import Decimal, getcontext
from exceptions import PairNotFound
import json
from adapters import *

# from django.core.cache import cache

#
# Someguy123's Ultimate Python Exchange API
# Modified for Flask
# Released under the GNU AGPL
#


getcontext().prec = 40



# avoid initializing an adapter more than once
ADAPTERS = {}

# which adapter can get us the price for a certain pair?
PAIRS = {
    # 'usd_btc': PoloniexAdapter,
    'usd_btc': HuobiAdapter,
#    'eur_btc': BTCEAdapter,
#    'usd_ltc': BTCEAdapter,
    'btc_ltc': BittrexAdapter,
#    'rur_btc': BTCEAdapter,
    'btc_eth': BittrexAdapter,
    'btc_sbd': BittrexAdapter,
    'btc_steem': BittrexAdapter,
    'btc_hive': BittrexAdapter,
    'btc_hbd': BittrexAdapter,
    'btc_eos': HuobiAdapter,
    'btc_golos': BittrexAdapter,
    'btc_gbg': BittrexAdapter,
    'btc_xzc': BittrexAdapter,
    'btc_sys': BittrexAdapter,
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
        raise PairNotFound('pair {} was not found'.format(pair))

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


