#! /usr/bin/env python

import time
try:
	import re2 as re
except:
	import re

import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr, is_channel

class Afrabot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
		self.nick = nickname.lower()
		self.lastopen = None
		self.chaossternchen = []

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        nick = e.source.nick
		target = e.target if is_channel(e.target) else nick
		line = e.arguments[0]
        a = line.split(":", 1)
        if len(a) > 1 and a[0].lower() == self.nick:
            self.do_command(e, a[1].strip().lower(), nick, target)
			return
		
		match = re.match('^({})? *: *chaos-?([☆★☼☀*]|sternchen) *: ?(.*)$'.format(self.nick), line)
		if match:
			newcs = match.group(3)
			self.chaossternchen.append(newcs)
			c.privmsg(self.channel, 'Chaos-☆ Nr. {} notiert: {}'.format(len(self.chaossternchen), newcs))

    def on_dccmsg(self, c, e):
        c.privmsg("Störe meine Kreise nicht.")

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

    def do_command(self, e, cmd, nick, target):
        c = self.connection
		if cmd.startswith('open'):
			if '?' in cmd or '‽' in cmd:
				c.privmsg(self.channel, 'Space is open!')
				self.lastopen = time.ctime()
			else:
				if self.lastopen:
					c.privmsg(target, 'Space was last marked open on '+self.lastopen)
				else:
					c.privmsg(target, "I don't know when was the last time the space was open.")
		elif re.match('^genug pleniert[.!]{,5}$') or re.match('^plenum[?!‽.]{,5}$', cmd):
			cs = self.chaossternchen
			if 'genug' in cmd:
				self.chaossternchen = []
				c.privmsg(target, 'Plenum beendet.')
			else:
				c.privmsg(target, 'Aye! So far, there are {} Chaos-☆'.format(len(cs)) + ('.' if len(cs) == 0 else ':'))
			for entry in enumerate(cs):
				c.privmsg(target, 'Chaos-☆ {}: {}'.format(*entry))
		elif re.match('^help[?!‽.]*$', cmd):
			c.privmsg(target, """
""")
		c.notice(nick, 'I don\'t know what you mean with "{}"'.format(cmd))

def main():
    import sys
    if len(sys.argv) != 4:
        print("Usage: testbot <server[:port]> <channel> <nickname>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = TestBot(channel, nickname, server, port)
    bot.start()

if __name__ == "__main__":
    main()
