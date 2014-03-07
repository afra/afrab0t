#! /usr/bin/env python

import time
import random
import datetime
try:
	import re2 as re
except:
	import re

import requests
from bs4 import UnicodeDammit
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr, is_channel

INSULTS = [
    "You silly, twisted boy you.",
    "What, what, what, what, what, what, what, what, what, what?",
    "Hold it up to the light --- not a brain in sight!",
    "You do that again and see what happens...",
    "Harm can come to a young lad like that!",
    "You gotta go owwwww!",
    "I think ... err ... I think ... I think I'll go home",
    "Maybe if you used more than just two fingers...",
    "I've seen penguins that can type better than that.",
    "You speak an infinite deal of nothing",
    "And you call yourself a Rocket Scientist!",
    "Where did you learn to type?",
    "Are you on drugs?",
    "My pet ferret can type better than you!",
    "You type like i drive.",
    "Do you think like you type?",
    "Your mind just hasn't been the same since the electro-shock, has it?",
		]

class Testbot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		self.channel = channel
		self.nick = nickname.lower()
		self.lastopen = None
		self.chaossternchen = []
		self.catpiccache = []
		self.moincount = 0

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
		
		m = re.findall('(^|\W)(c-?base)(\W|$)', line, re.IGNORECASE)
		for match in m:
			if match[1] != 'c-base':
				c.privmsg(target, "It's c-base, not "+match[1]+'. '+random.choice(INSULTS))
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

	bot = Testbot(channel, nickname, server, port)
	bot.start()

if __name__ == "__main__":
	main()
