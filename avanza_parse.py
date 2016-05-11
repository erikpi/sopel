#!/usr/bin/python
# -*- coding: utf-8 -*-
# Module for sopel. Will fetch html from avanza.se and display latest data in your IRC channel.
# https://github.com/senilio/sopel

import sys
import os
import requests, json
import re
import locale

locale.setlocale(locale.LC_ALL, 'sv_SE')

def avanzaStringToFloat(inputString):
    try:
        f = float(inputString.replace(',', '.'))
    except:
        f = 0.0
    return f

def avanzaStringToInt(inputString):
    try:
        return int(re.sub('[^0-9]', '', inputString))
    except ValueError:
        return 0
    
def getTickerInfoAvanza(ticker, quick=False):
    base_url = u'https://www.avanza.se/ab/component/orderbook_search/?query={0}&collection=STOCK&onlyTradable=false&pageType=stock&orderTypeView='

    r = requests.get(base_url.format(ticker))
    if not r.status_code == 200:
        return None

    response = r.text
    data = json.loads(response)
    if not data:
        return None
    firstObj = data[0]
    info_url = firstObj.get('url')

    stockUrl = 'https://www.avanza.se{0}'.format(info_url)
    r = requests.get(stockUrl)

    res = {}
    res['url'] = stockUrl
    res['urlAbout'] = stockUrl.replace('om-aktien', 'om-bolaget')

    if quick is True:
        return res  

    lastPriceUpdate = re.findall('<span class="lastPrice SText bold"><span class="pushBox roundCorners3" title="Senast uppdaterad: ([0-9:]+)">([,\d]+)</span></span>', r.text)
    res['lastUpdate'] = lastPriceUpdate[0][0]
    res['lastPrice'] = avanzaStringToFloat(lastPriceUpdate[0][1])

    dataOrderbookName = re.findall('data-orderbook_name="(.*)"', r.text)
    res['orderBookName'] = dataOrderbookName[0]

    dataOrderbookCurrency = re.findall('data-orderbook_currency="(.*)"', r.text)
    res['orderBookCurrency'] = dataOrderbookCurrency[0]
    
    changePercent = re.findall('<span class="changePercent SText bold \w+">(.*)\s+\%</span>', r.text)
    res['changePercent'] = avanzaStringToFloat(changePercent[0])
     
    owners = re.findall('hos Avanza</span></dt>\r\n\s+<dd><span>(.*)</span></dd>', r.text)
    res['numOwners'] = avanzaStringToInt(owners[0])
    
    networth = re.findall('Börsvärde MSEK</span></dt>\r\n\s+<dd><span>(.*)</span></dd>', r.text)
    res['networth'] = avanzaStringToInt(networth[0])

    highestPrice = re.findall('<span class="highestPrice SText bold">(.*)</span>', r.text)
    res['highestPrice'] = avanzaStringToFloat(highestPrice[0])

    lowestPrice = re.findall('<span class="lowestPrice SText bold">(.*)</span>', r.text)
    res['lowestPrice'] = avanzaStringToFloat(lowestPrice[0])

    totalVolumeTraded = re.findall('<span class="totalVolumeTraded SText bold">(.*)</span>', r.text)
    res['totalVolumeTraded'] = avanzaStringToInt(totalVolumeTraded[0])

    totalValueTraded = re.findall('<span class="totalValueTraded">(.*)</span>', r.text)
    res['totalValueTraded'] = avanzaStringToInt(totalValueTraded[0])

    return res

def getOutput(res):
    if res['changePercent'] < 0:
        change = '{0:n}%'.format(res['changePercent'])
        try:
            change = formatting.color(change, formatting.colors.RED)
        except:
            pass
    elif res['changePercent'] > 0:
        change = '{0:+n}%'.format(res['changePercent'])
        try:
            change = formatting.color(change, formatting.colors.GREEN)
        except:
            pass
    else:
        change = "0.00%"

    msg = u'{0}: {1} {2} ({3}). '.format(res['orderBookName'], locale.currency(res['lastPrice'], symbol=False), res['orderBookCurrency'], change)
    msg += u'Day range: {0}-{1}. '.format(locale.currency(res['lowestPrice'], symbol=False), locale.currency(res['highestPrice'], symbol=False))
    msg += u'Day volume: {0:n}. '.format(res['totalVolumeTraded'])
    msg += u'Day revenue: {0:n} {1}. '.format(res['totalValueTraded'], res['orderBookCurrency'])
    msg += u'Shareholders: {0:n}. (Updated: {1})'.format(res['numOwners'], res['lastUpdate'])
    msg += u'Net Worth: {0:n}. '.format(res['networth'])
    return msg

def getAvanzaReportDates(ticker):
    da = getTickerInfoAvanza(ticker, quick=True)
    if da is None:
        return da

    r = requests.get(da['urlAbout'])

    t = re.findall('<h3 class="bold">Kommande(.*?)<h3 class="bold">Tidigare', r.text ,re.DOTALL|re.MULTILINE)
    output = []
    if t:
        da = re.sub('\s{2,}', '', t[0])
        info = re.findall('<dt><span>([-\w]+?)</span></dt><dd><span>(.*?)</span></dd>', da, re.DOTALL|re.MULTILINE)

        for i in info:
            output.append(i[0] + ' : ' + re.sub('<.*?>', '  ', i[1]))

    return output

if __name__ == "__main__":
    # test parsing function without sopel bot
    tickers = 'kambi,pricer,knebv'
    tickers = tickers.split(',')
    for t in tickers:
        try:
            da = getTickerInfoAvanza(t)
            if da is None:
                raise TypeError('I need a valid ticker name')
            msg = getOutput(da)
            print repr(msg)
        except (IndexError, TypeError) as e:
            print e.message

    try:
        da = getAvanzaReportDates('telia')
        if da is None:
            raise TypeError('I need a valid ticker name')
        for r in da[:5]:
            print r
    except (IndexError, TypeError) as e:
        print e.message

    
    sys.exit(0)

from sopel import module
from sopel import formatting

@module.commands('a', 'avanza', 'aza', 'ava', 'az')
def avanza(bot, trigger):
    ticker = trigger.group(2)
    if not ticker:
        ticker = '123'

    tickers = ticker.split(',')
    for ticker in tickers:
        try:
            res = getTickerInfoAvanza(ticker)
            if res is None:
                raise TypeError('I need a valid ticker name. My lady.')
            msg = getOutput(res)
            bot.say(msg)

        except (IndexError, TypeError) as e:
            bot.say(e.message)

@module.commands('azr')
def avanzar(bot, trigger):
    try:
        ticker = trigger.group(2)
        if not ticker:
            ticker = '123'

        res = getAvanzaReportDates(ticker)
        if res is None:
            raise TypeError('I need a valid ticker name.')
        for r in res[:5]:
            bot.say(r)

    except (IndexError, TypeError) as e:
        bot.say(e.message)
