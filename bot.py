#!/usr/bin/env python3
# Simple Discord SelfBot
# Created By Viloid ( github.com/vsec7 )
# Use At Your Own Risk


        import requests, random, sys, yaml, time, itertools


class Discord:

    def __init__(self, token):
        self.token = token
        self.base = "https://discord.com/api/v9"
        self.auth = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

    def getMe(self):
        u = requests.get(self.base + "/users/@me", headers=self.auth).json()
        return u

    def getMessage(self, cid, l):
        u = requests.get(self.base + "/channels/" + str(cid) + "/messages?limit=" + str(l), headers=self.auth).json()
        return u

    def sendMessage(self, cid, txt):
        u = requests.post(self.base + "/channels/" + str(cid) + "/messages", headers=self.auth, json={'content': txt}).json()
        return u

    def replyMessage(self, cid, mid, txt):
        u = requests.post(self.base + "/channels/" + str(cid) + "/messages", headers=self.auth, json={'content': txt, 'message_reference': {'message_id': str(mid)}}).json()
        return u

    def deleteMessage(self, cid, mid):
        u = requests.delete(self.base + "/channels/" + str(cid) + "/messages/" + str(mid), headers=self.auth)
        return u


# ---------- CUSTOM MODE STATE (round-robin, no repeats until full cycle) ----------
custom_messages = []
_ub_turn = True   # toggle: True = giliran kirim "ub", False = giliran kirim chat random


def load_custom(path="custom.txt"):
    """Baca custom.txt, pisahin baris 'ub' dari kalimat chat. Format tetep ub->chat->ub->chat."""
    global custom_messages
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    custom_messages = [l for l in lines if l.lower() != "ub"]
    if not custom_messages:
        print("[!] custom.txt kosong atau gaada kalimat selain 'ub'!")
        sys.exit()


def next_custom():
    """Selang-seling: ub, lalu chat random, ub, chat random, dst."""
    global _ub_turn
    if _ub_turn:
        _ub_turn = False
        return "ub"
    else:
        _ub_turn = True
        return random.choice(custom_messages)


def quote():
    u = requests.get("https://raw.githubusercontent.com/lakuapik/quotes-indonesia/master/raw/quotes.min.json").json()
    return random.choice(list(u))['quote']


def simsimi(lc, txt):
    u = requests.post("https://api.simsimi.vn/v1/simtalk", data={'lc': lc, 'text': txt}).json()
    return u['message']


# ---------- FITUR BARU: AUTO-STOP KALO DI-TAG ----------
# Nyimpen id pesan terakhir yang udah "dianggep lama" per channel, biar tag yang
# udah ada dari sebelum bot start (atau sebelum stop terakhir) gak ke-detect ulang.
_baseline_msg_id = {}


def init_baseline(Bot, chan):
    """Panggil sekali pas bot start: catet id pesan terbaru di channel sbg baseline."""
    try:
        res = Bot.getMessage(chan, 1)
        if isinstance(res, list) and res:
            _baseline_msg_id[chan] = int(res[0]['id'])
        else:
            _baseline_msg_id.setdefault(chan, 0)
    except Exception:
        _baseline_msg_id.setdefault(chan, 0)


def is_mentioned(Bot, chan, me_id, check_last=5):
    """
    Cek `check_last` pesan terakhir di channel.
    Cuma pesan yang id-nya LEBIH BARU dari baseline (dicatet pas start) yang dihitung,
    jadi tag lama yang belum ke-hapus gak bikin bot berhenti berulang-ulang.
    Return (True, msg) kalau ada pesan BARU yang nge-mention akun bot ini.
    """
    try:
        res = Bot.getMessage(chan, check_last)
    except Exception:
        return False, None

    if not isinstance(res, list):
        return False, None

    baseline = _baseline_msg_id.get(chan, 0)

    for msg in res:
        try:
            if int(msg['id']) <= baseline:
                continue  # pesan lama, skip
        except (KeyError, ValueError):
            continue

        for m in msg.get('mentions', []):
            if str(m.get('id')) == str(me_id):
                return True, msg

        # jaga-jaga kalo mention ditulis manual sbg text <@id> / <@!id>
        content = msg.get('content', '') or ''
        if "<@{}>".format(me_id) in content or "<@!{}>".format(me_id) in content:
            return True, msg

    return False, None


def main():
    with open('config.yaml') as cfg:
        conf = yaml.load(cfg, Loader=yaml.FullLoader)

    if not conf['BOT_TOKEN']:
        print("[!] Please provide discord token at config.yaml!")
        sys.exit()

    if not conf['CHANNEL_ID']:
        print("[!] Please provide channel id at config.yaml!")
        sys.exit()

    mode = conf['MODE']
    simi_lc = conf['SIMSIMI_LANG']
    delay = conf['DELAY']
    del_after = conf['DEL_AFTER']
    repost_last = conf['REPOST_LAST_CHAT']

    # opsional di config.yaml: STOP_ON_MENTION: true/false (default: true)
    stop_on_mention = conf.get('STOP_ON_MENTION', True)
    # opsional: mau exit total atau cuma pause & lanjut manual
    check_last = conf.get('MENTION_CHECK_LAST', 5)

    if not mode:
        mode = "quote"

    if not simi_lc:
        simi_lc = "id"

    if not repost_last:
        repost_last = "100"

    if mode == "custom":
        load_custom()

    # --- catet baseline (pesan terakhir yg udah ada) tiap channel, sekali aja pas start ---
    if stop_on_mention:
        for token in conf['BOT_TOKEN']:
            for chan in conf['CHANNEL_ID']:
                init_baseline(Discord(token), chan)
        print("[i] Baseline mention udah dicatet. Bot cuma bakal stop kalo ada tag BARU (setelah start ini).")

    while True:
        for token in conf['BOT_TOKEN']:
            try:
                for chan in conf['CHANNEL_ID']:

                    Bot = Discord(token)
                    me_data = Bot.getMe()
                    me = me_data['username'] + "#" + me_data['discriminator']
                    me_id = me_data.get('id')

                    # --- cek mention dulu sebelum ngirim apapun ---
                    if stop_on_mention:
                        tagged, msg = is_mentioned(Bot, chan, me_id, check_last)
                        if tagged:
                            author = msg.get('author', {}).get('username', 'someone')
                            print("[!!!] Bot {} ke-tag oleh '{}' di channel {}. Bot dihentikan.".format(me, author, chan))
                            sys.exit(0)

                    if mode == "quote":
                        q = quote()
                        send = Bot.sendMessage(chan, q)
                        print("[{}][{}][QUOTE] {}".format(me, chan, q))
                        if del_after:
                            Bot.deleteMessage(chan, send['id'])
                            print("[{}][DELETE] {}".format(me, send['id']))

                    elif mode == "repost":
                        res = Bot.getMessage(chan, random.randint(1, repost_last))
                        getlast = list(reversed(res))[0]
                        send = Bot.sendMessage(chan, getlast['content'])
                        print("[{}][{}][REPOST] {}".format(me, chan, getlast['content']))
                        if del_after:
                            Bot.deleteMessage(chan, send['id'])
                            print("[{}][DELETE] {}".format(me, send['id']))

                    elif mode == "simsimi":
                        res = Bot.getMessage(chan, "1")
                        getlast = list(reversed(res))[0]
                        simi = simsimi(simi_lc, getlast['content'])

                        if conf['REPLY']:
                            send = Bot.replyMessage(chan, getlast['id'], simi)
                            print("[{}][{}][SIMSIMI] {}".format(me, chan, simi))
                        else:
                            send = Bot.sendMessage(chan, simi)
                            print("[{}][{}][SIMSIMI] {}".format(me, chan, simi))

                        if del_after:
                            Bot.deleteMessage(chan, send['id'])
                            print("[{}][DELETE] {}".format(me, send['id']))

                    elif mode == "custom":
                        c = next_custom()
                        send = Bot.sendMessage(chan, c)
                        print("[{}][{}][CUSTOM] {}".format(me, chan, c))
                        if del_after:
                            Bot.deleteMessage(chan, send['id'])
                            print("[{}][DELETE] {}".format(me, send['id']))

                    time.sleep(3)  # jeda antar pesan (sebelum delay besar tiap putaran)

            except SystemExit:
                raise
            except Exception as e:
                print(f"[Error] {token} : INVALID TOKEN / KICKED FROM GUILD! ({e})")

        if isinstance(delay, (list, tuple)) and len(delay) == 2:
            wait = random.randint(int(delay[0]), int(delay[1]))
        elif isinstance(delay, str) and "," in delay:
            lo, hi = delay.replace("[", "").replace("]", "").split(",")
            wait = random.randint(int(lo.strip()), int(hi.strip()))
        else:
            wait = int(delay)

        print("-------[ Delay for {} seconds ]-------".format(wait))
        time.sleep(wait)


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f"{type(err).__name__} : {err}")