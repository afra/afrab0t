#! /usr/bin/env python

import time
try:
	import re2 as re
except:
	import re

import requests
from bs4 import UnicodeDammit
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr, is_channel
import pyimgur
import praw

class Afrabot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		self.channel = channel
		self.nick = nickname.lower()
		self.lastopen = None
		self.chaossternchen = []
		self.catpiccache = []

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")

	def on_welcome(self, c, e):
		c.join(self.channel)

	def on_privmsg(self, c, e):
		self.do_command(e, e.arguments[0], e.source.nick, e.source.nick)

	def on_pubmsg(self, c, e):
		nick = e.source.nick
		target = e.target if is_channel(e.target) else nick
		line = UnicodeDammit(e.arguments[0]).unicode_markup
		a = line.split(":", 1)
		if len(a) > 1 and a[0].lower() == self.nick:
			self.do_command(e, a[1].strip().lower(), nick, target)
			return
		
		match = re.match('^({} *:)? *chaos-?([☆★☼☀*]|sternchen) *: ?(.*)$'.format(self.nick), line)
		if match:
			newcs = match.group(3)
			self.chaossternchen.append(newcs)
			c.privmsg(self.channel, 'Chaos-☆ Nr. {} notiert: {}'.format(len(self.chaossternchen), newcs))
			return

		if line.startswith('.wiki '):
			wikipage = line[len('.wiki '):].strip()
			if re.match('^[-_+\w]+$', wikipage):
				wikiurl = 'https://afra-berlin.de/dokuwiki/doku.php?id={}'.format(wikipage)
				if 'Dieses Thema existiert noch nicht' in requests.get(wikiurl).text:
					c.privmsg(target, "I'm sorry, I can't find a wiki page with that name.")
				else:
					c.privmsg(target, wikiurl)
			else:
				c.privmsg(target, 'Try to troll somebot else.')
			return

		if line == 'wat?':
			c.privmsg(target, "I don't have a clue.")
			return
		if re.match('^hail eris[.!]* ', line.lower()):
			c.privmsg(target, "All Hail Discordia!")
			return
		if re.search('https?://[-a-z0-9.]*facebook.com', line.lower()):
			c.privmsg(target, 'A facebook link? srsly? Get some self-respect!')
			return
		match = re.search('https?://pr0gramm.com/#(newest/\*/[0-9/]*)', line.lower())
		if match:
			c.privmsg(target, 'Fixed that pr0gramm link for you: http://pr0gramm.com/static/'+match.group(1))
			return

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
				if cmd.count('?') >= 5:
					c.privmsg(self.channel, 'afrabot: open?')
					return
				if self.lastopen:
					if self.spaceopen:
						c.privmsg(target, 'Space was last marked open on '+self.lastopen)
					else:
						c.privmsg(target, 'Space was last marked closed on '+self.lastopen)
				else:
					c.privmsg(target, "I don't know when was the last time the space was open.")
			else:
				if cmd.count('!') > 5:
					c.privmsg(target, 'u mad bro?')
					return
				c.privmsg(self.channel, 'Space is open!')
				self.lastopen = time.ctime()
				self.spaceopen = True
			return
		if cmd.startswith('closed'):
			if '?' in cmd or '‽' in cmd:
				if self.lastopen:
					if self.spaceopen:
						c.privmsg(target, 'Space was last marked open on '+self.lastopen)
					else:
						c.privmsg(target, 'Space was last marked closed on '+self.lastopen)
				else:
					c.privmsg(target, "I don't know when was the last time the space was closed.")
			else:
				if cmd.count('!') > 5:
					c.privmsg(target, 'u mad bro?')
					return
				c.privmsg(self.channel, 'Space is closed! Please remember to follow the shutdown protocol.')
				if target != self.channel:
					c.privmsg(target, 'Please remember to follow the shutdown protocol.')
				self.lastopen = time.ctime()
				self.spaceopen = False
			return
		if re.match('^ *genug +pleniert[.!]{,5}$', cmd) or re.match('^plenum[?!‽.]{,5}$', cmd):
			cs = self.chaossternchen
			if 'genug' in cmd:
				self.chaossternchen = []
				c.privmsg(target, 'Plenum beendet.')
			else:
				c.privmsg(target, 'Aye! So far, there are {} Chaos-☆'.format(len(cs)) + ('.' if len(cs) == 0 else ':'))
			for entry in enumerate(cs):
				c.privmsg(target, 'Chaos-☆ {}: {}'.format(*entry))
			return
		csmatch = re.match('^ *(delete|remove) +chaos-?([☆★☼☀*]|sternchen) *([0-9]+)[.!]{,5}$', cmd)
		if csmatch:
			try:
				num = int(csmatch.group(3))
				del self.chaossternchen[num]
				c.privmsg(target, 'Chaos-☆ {} deleted.'.format(num))
			except:
				c.privmsg(target, 'wut?')
			return
		if re.match('^help[?!‽.]*$', cmd):
			helptext = """open|closed? - query whether space is open
open|closed - set space open/closed
chaos*: [foobar] - add plenum topic
delete chaos* [num] - delete plenum topic number [n]
shutdown - list things to do when closing the space
plenum - list plenum topics
"""
			for line in helptext.splitlines():
				c.privmsg(target, line)
			return
		if re.match('^shutdown[?‽]*$', cmd):
			helptext = """* Fenster schließen (Beim rechten Fenster muss ein Hebel unten am Fenster betätigt werden. Bitte stellt sicher, dass beide Fenster dicht geschlossen sind.)
* Tische aufräumen und bei Bedarf kurz abwischen
* Geschirr spülen
* Kühlschrank auffüllen
* Heizung auf eine angemessene Stufe stellen (Winter: 2-3)
* Lampen, Computer, Boxen, Beamer, Kochplatte, Ofen, *Wasserkocher*, Laser abschalten
* Gucken, ob ralisi noch Geschirr abwäscht
* Müll mit runter nehmen
* Raum-, Aufgangs- und Haustür verschließen
"""
			for line in helptext.splitlines():
				c.privmsg(target, line)
			return
		if cmd == 'ponies?':
			c.privmsg(target, 'yes please!')
			return
		if re.match('^ *tell +afrab[o0]t +', cmd):
			c.privmsg(target, 'what is your problem?')
			return
		if cmd.rstrip('?') in ('where', 'location', 'wo'):
			c.privmsg(target, 'AfRA Berlin e.V. is located at Herzbergstr. 55, 10365 Berlin, 2.HH/Aufgang B, 3. floor on the left (Rm 3.08). Public transport: Tram M8, 21, 37 & Bus 256 → Herzbergstr./Siegfriedstr.')
			return
		if cmd.rstrip('?!.') in ('cats', 'katzen', 'kittens', 'kätzchen'):
			try:
				r = praw.Reddit(user_agent='AfRAb0t v0.23')
				submissions = r.get_subreddit('cats').get_hot(limit=50)
				item = next(s for s in submissions if s.url not in self.catpiccache and not s.stickied and not s.is_self)
				self.catpiccache.append(item.url)
				c.privmsg(target, 'Got some cats for you: '+item.url)
			except StopIteration:
				c.privmsg(target, 'The intertubes are empty.')
			return
		c.notice(nick, 'I don\'t know what you mean with "{}"'.format(cmd))

def main():
	import sys
	if len(sys.argv) != 4:
		print("Usage: afrabot <server[:port]> <channel> <nickname>")
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

	bot = Afrabot(channel, nickname, server, port)
	bot.start()

if __name__ == "__main__":
	main()
