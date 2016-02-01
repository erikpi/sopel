#!/usr/bin/python

# Module for sopel. Will fetch html from avanza.se and display latest data in your IRC channel.
# https://github.com/senilio/sopel

import sys
import os
import requests, json
from sopel import module
from sopel import formatting

@module.commands('a', 'avanza', 'aza', 'ava', 'az')
def avanza(bot, trigger):

   try:
      ticker = trigger.group(2)
      base_url_pre = 'https://www.avanza.se/ab/component/orderbook_search/?query='
      base_url_post = '&collection=STOCK&onlyTradable=false&pageType=stock&orderTypeView='
      if not ticker:
         ticker = '123'

      r = requests.get(base_url_pre + ticker + base_url_post)
      info_url = r.text.split('":"')[1].split('","')[0]

      r = requests.get('https://www.avanza.se' + info_url)

      for i in iter(r.text.splitlines()):
         if 'lastPrice' in i and 'Senast uppdaterad' in i:
            lastPrice = i.split('>')[2].split('<')[0]
         if 'data-orderbook_name' in i:
            longName = i.split('=')[1][1:-1]
         if 'changePercent' in i and '%' in i:
            changePercent = i.split('>')[1].split('<')[0][:-2]
         if 'data-orderbook_currency' in i:
            currency = i.split('=')[1][1:-1]
         if 'lastPrice' in i and 'uppdaterad' in i:
            lastupdate = i.split('uppdaterad: ')[1].split('"')[0]

      # Format percentChange
      if ',' in changePercent:
         changePercent = float(changePercent.replace(',','.'))

      if changePercent < 0:
         change = formatting.color(str(changePercent) +'%', formatting.colors.RED)
      elif changePercent > 0:
         change = formatting.color('+' + str(changePercent) + '%', formatting.colors.GREEN)
      else:
         change = "0.00%"

      bot.say('' + longName + ' quote is: ' + lastPrice + ' ' + currency + ' (' + change + '). Updated ' + lastupdate + '.')

   except IndexError, TypeError:
      bot.say('I need a valid ticker name.')

