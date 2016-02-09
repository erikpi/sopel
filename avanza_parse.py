#!/usr/bin/python
# -*- coding: utf-8 -*-
# Module for sopel. Will fetch html from avanza.se and display latest data in your IRC channel.
# https://github.com/senilio/sopel

import sys
import os
import requests, json
import re

def avanzaStringToFloat(inputString):
    return float(inputString.replace(',', '.'))  

def avanzaStringToInt(inputString):
    return int(re.sub('[^0-9]', '', inputString))
    
def getTickerInfoAvanza(ticker, quick=False):
    base_url = 'https://www.avanza.se/ab/component/orderbook_search/?query={0}&collection=STOCK&onlyTradable=false&pageType=stock&orderTypeView='

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

    lastPriceUpdate = re.findall('<span class="lastPrice SText bold"><span class="pushBox roundCorners3" title="Senast uppdaterad: ([0-9:]+)">(\d+),(\d+)</span></span>', r.text)
    res['lastUpdate'] = lastPriceUpdate[0][0]
    humanReadable = '{0},{1} kr'.format(*lastPriceUpdate[0][1:])
    res['lastPrice'] = humanReadable

    dataOrderbookName = re.findall('data-orderbook_name="(.*)"', r.text)
    res['orderBookName'] = dataOrderbookName[0]

    dataOrderbookCurrency = re.findall('data-orderbook_currency="(.*)"', r.text)
    res['orderBookCurrency'] = dataOrderbookCurrency[0]
    
    changePercent = re.findall('<span class="changePercent SText bold \w+">(.*)\s+\%</span>', r.text)
    res['changePercent'] = avanzaStringToFloat(changePercent[0])
     
    owners = re.findall('hos Avanza</span></dt>\r\n\s+<dd><span>(.*)</span></dd>', r.text)
    res['numOwners'] = avanzaStringToInt(owners[0])

    highestPrice = re.findall('<span class="highestPrice SText bold">(.*)</span>', r.text)
    res['highestPrice'] = avanzaStringToFloat(highestPrice[0])

    lowestPrice = re.findall('<span class="lowestPrice SText bold">(.*)</span>', r.text)
    res['lowestPrice'] = avanzaStringToFloat(lowestPrice[0])

    totalVolumeTraded = re.findall('<span class="totalVolumeTraded SText bold">(.*)</span>', r.text)
    res['totalVolumeTraded'] = avanzaStringToInt(totalVolumeTraded[0])

    return res

def getOutput(res):
    if res['changePercent'] < 0:
        change = '{0}%'.format(res['changePercent'])
        try:
            change = formatting.color(change, formatting.colors.RED)
        except:
            pass
    elif changePercent > 0:
        change = '+{0}%'.format(res['changePercent'])
        try:
            change = formatting.color(change, formatting.colors.GREEN)
        except:
            pass
    else:
        change = "0.00%"

    msg = '{0}: {1} {2} ({3}). '.format(res['orderBookName'], res['lastPrice'], res['orderBookCurrency'], change)
    msg += 'Day range: {0}-{1}. '.format(res['lowestPrice'], res['highestPrice'])
    msg += 'Day volume: {0}. '.format(res['totalVolumeTraded'])
    msg += 'Shareholders: {0}. (Updated: {1})'.format(res['numOwners'], res['lastUpdate'])
    return msg


if __name__ == "__main__":
    # test parsing function without sopel bot
    da = getTickerInfoAvanza('pricer')
    msg = getOutput(da)
    print msg
    sys.exit(0)

from sopel import module
from sopel import formatting

@module.commands('a', 'avanza', 'aza', 'ava', 'az')
def avanza(bot, trigger):
    try:
        ticker = trigger.group(2)
        if not ticker:
            ticker = '123'

        res = getTickerInfoAvanza(ticker)
        msg = getOutput(res)
        bot.say(msg)

    except IndexError, TypeError:
        bot.say('I need a valid ticker name.')
