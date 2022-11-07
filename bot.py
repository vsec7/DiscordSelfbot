#!/usr/bin/env python3
# Simple Discord SelfBot
# Created By Viloid ( github.com/vsec7 )
# Use At Your Own Risk

from api import Discord
import requests, random, sys, yaml, time


def quote():
  u = requests.get("https://raw.githubusercontent.com/lakuapik/quotes-indonesia/master/raw/quotes.min.json").json()
  return random.choice(list(u))['quote']


if __name__ == "__main__":

  with open('config.yaml') as cfg:
    conf = yaml.load(cfg, Loader=yaml.FullLoader)
    
  token = conf['BOT_TOKEN']
  chan = conf['CHANNEL_ID']
  mode = conf['MODE']
  delay = conf['DELAY']
  del_after = conf['DEL_AFTER']
  repost_last = conf['REPOST_LAST_CHAT']
  
  if not token:
    print("[!] Please provide discord token at config.yaml !")
    sys.exit()
    
  if not chan:
    print("[!] Please provide channel id at config.yaml !")
    sys.exit()
    
  if not mode: 
    mode = "quote"
    
  if not repost_last: 
    repost_last = "100"
    
  Bot = Discord(token)
  gm = Bot.getMe()
  
  me = gm['username'] + "#" + gm['discriminator']
    
  while True:
    
    if mode == "quote":
      q = quote()
      send = Bot.sendMessage(chan, q)
      print("[{}][QUOTE] {}".format(me, q))
      
      if del_after:
        delmsg = Bot.deleteMessage(chan, send['id'])
        print("[{}][DELETE] {}".format(me, send['id']))       

    elif mode == "repost":
      res = Bot.getMessage(chan, repost_last)
      getlast = list(reversed(res))[0]
      
      send = Bot.sendMessage(chan, getlast['content'])
      print("[{}][REPOST] {}".format(me, getlast['content']))

      if del_after:
        delmsg = Bot.deleteMessage(chan, send['id'])
        print("[{}][DELETE] {}".format(me, send['id']))
  
    print("-------[ Delay for {} seconds ]-------".format(delay))

    time.sleep(delay)
