#!/usr/bin/env python3
# Simple Discord API Wrapper
# Created By Viloid ( github.com/vsec7 )
# Use At Your Own Risk

import requests

class Discord:

  def __init__(self, t):
    self.base = "https://discord.com/api/v9"
    self.auth = { 'authorization': t }
    
  def getMe(self):
    u = requests.get(self.base + "/users/@me", headers=self.auth).json()
    return u
    
  def getMessage(self, cid, l):
    u = requests.get(self.base + "/channels/" + str(cid) + "/messages?limit=" + str(l), headers=self.auth).json()
    return u
    
  def sendMessage(self, cid, txt):    
    u = requests.post(self.base + "/channels/" + str(cid) + "/messages", headers=self.auth, json={ 'content': txt }).json()
    return u

  def replyMessage(self, cid, mid, txt):    
    u = requests.post(self.base + "/channels/" + str(cid) + "/messages", headers=self.auth, json={ 'content': txt, 'message_reference': { 'message_id': str(mid) } }).json()
    return u

  def deleteMessage(self, cid, mid):
    u = requests.delete(self.base + "/channels/" + str(cid) + "/messages/" + str(mid), headers=self.auth)
    return u

  def joinGuild(self, c):
    u = requests.post(self.base + "/invites/" + str(c), headers=self.auth, json={}).json()
    return u

  def leaveGuild(self, i):
    u = requests.delete(self.base + "/users/@me/guilds/" + str(i), headers=self.auth)
    return u
