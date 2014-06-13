#! /usr/bin/env python

import time
import datetime
try:
	import re2 as re
except:
	import re
from random import random
import requests
from bs4 import UnicodeDammit
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr, is_channel
import pyimgur
import praw
import sqlite3
from contextlib import contextmanager
import settings

def log(*args):
	print(time.strftime('\x1B[93m[%m-%d %H:%M:%S]\x1B[0m'), *args+('\x1B[0m',))

class Afrabot(irc.bot.SingleServerIRCBot):
	def __init__(self, db, channel, nickname, server, port=6667):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		self.db = db
		self.channel = channel
		self.nick = nickname.lower()
		self.lastopen = None
		self.chaossternchen = []
		self.catpiccache = []
		self.reddit = praw.Reddit(user_agent='AfRAb0t/0.23 by jaseg')
		self.moincount = 0

	def send(self, target, msg):
		self.connection.privmsg(target, msg)

	def sendchan(self, msg):
		self.connection.privmsg(self.channel, msg)

	def identify(self):
		log('\033[92mIdentifying\033[0m')
		self.send('NickServ', 'identify '+settings.NICKSERV_PASSWORD)
	
	def regain(self):
		log('\033[92mRegaining\033[0m')
		self.send('NickServ', ' '.join(('regain', self.nick, settings.NICKSERV_PASSWORD)))
	
	def get_op(self, op=True):
		line = ' '.join(('OP' if op else 'DEOP', self.channel, self.nick))
		print(line)
		self.send('ChanServ', line)
		time.sleep(5.0)

	@contextmanager
	def op(self):
		log('\033[91mGetting OP\033[0m')
		self.get_op()
		yield
		log('\033[92mYielding OP\033[0m')
		self.get_op(False)

	def kick(self, nick, reason=''):
		with self.op():
			log('\033[91mKicking {}\033[0m ({})'.format(nick, reason))
			self.connection.kick(self.channel, nick, reason)

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")
		self.regain()

	def on_welcome(self, c, e):
		c.join(self.channel)
		self.send('jaseg', 'afrab0t online')
		self.identify()

	def on_privnotice(self, c, e):
		log('\033[37mPRIVNOTICE {}→{}\033[0m'.format(e.source.nick, ' '.join(e.arguments)))

	def on_pubnotice(self, c, e):
		log('\033[37mPUBNOTICE {}→{}\033[0m'.format(e.source.nick, ' '.join(e.arguments)))

	def on_privmsg(self, c, e):
		log('\033[37mPRI {}→{}\033[0m'.format(e.source.nick, ' '.join(e.arguments)))
		def dm(msg):
			self.send(e.source.nick, msg)
		self.do_command(e, e.arguments[0], e.source.nick, e.source.nick, dm, dm)

	def on_pubmsg(self, c, e):
		nick = e.source.nick
		target = e.target if is_channel(e.target) else nick
		def reply(msg):
			self.send(target, msg)
		def dm(msg):
			self.send(nick, msg)
		line = UnicodeDammit(e.arguments[0]).unicode_markup
		log('\033[37mPUB {}→{}\033[0m'.format(nick, line))
		a = line.split(":", 1)
		if len(a) > 1 and a[0].lower() == self.nick:
			self.do_command(e, a[1].strip().lower(), nick, target, reply, dm)
			return

		# zeltofilter
		if 'zeltoph' in nick:
			return

		foo = settings.VIPS.get(nick, 0)
		if random() < foo:
			self.kick(nick)
	
		match = re.match('.*┻━┻.*', line)
		if match:
			reply('┬─┬ノ(ಠ_ಠノ)')
			return

		match = re.match('^({} *:)? *chaos-?([☆★☼☀*]|sternchen) *: ?(.*)$'.format(self.nick), line)
		if match:
			newcs = match.group(3)
			self.chaossternchen.append(newcs)
			self.sendchan('Chaos-☆ Nr. {} notiert: {}'.format(len(self.chaossternchen), newcs))
			return

		if line.startswith('.wiki '):
			wikipage = line[len('.wiki '):].strip()
			if re.match('^[-_+\w]+$', wikipage):
				wikiurl = 'http://afra-berlin.de/dokuwiki/doku.php?id={}'.format(wikipage)
				if 'Dieses Thema existiert noch nicht' in requests.get(wikiurl).text:
					reply("I'm sorry, I can't find a wiki page with that name.")
				else:
					reply(wikiurl)
			else:
				reply('Try to troll somebot else.')
			return

		if line == 'wat?':
			reply("I don't have a clue.")
			return
		if re.match('^hail eris[.!]* ', line.lower()):
			reply("All Hail Discordia!")
			return
		m = re.findall('(^|\s)?(gh?ah?nh?dh?ih?)(\s|$)?', line, re.IGNORECASE)
		for _1,match,_2 in m:
			if not re.match('(^|\s)?gandhi(\s|$)?', match, re.IGNORECASE):
				self.kick(nick, "It's spelled Gandhi")
				return
		if re.search('https?://[-a-z0-9.]*facebook.com', line.lower()):
			reply('A facebook link? srsly? Get some self-respect!')
			return
		match = re.search('https?://pr0gramm.com/#(newest/\*/[0-9/]*)', line.lower())
		if match:
			reply('Fixed that pr0gramm link for you: http://pr0gramm.com/static/'+match.group(1))
			return
		if line == 'moin':
			self.moincount += 1
			if self.moincount == 5:
				reply('moin')
			return
		else:
			self.moincount = 0
		if line.lstrip('.!#').startswith('eta '):
			eta = line[4:].strip()
			with self.db as db:
				db.execute("DELETE FROM etas WHERE nick=?", (nick,))
				if eta:
					db.execute("INSERT INTO etas VALUES (DATETIME('now'), ?, ?)", (nick, eta))
			dm('ETA registered. Thanks!')
			return
		if 'union' in line.lower():
			reply('Uniohon: https://www.youtube.com/watch?v=ym3Giin2C8k')
			return
		m = re.findall('(^|\s)(afra)(\s|$)', line, re.IGNORECASE)
		for _1,match,_2 in m:
			if match != 'AfRA' and match != 'afra' and random() < 0.1:
				reply("I'm sure you meant AfRA, not "+match)
				return

	def on_dccmsg(self, c, e):
		pass

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

	def do_command(self, e, cmd, nick, target, reply, dm):
		c = self.connection

		emoticontable = {
				':)': '☺',
# Some lines commented out due to lack of widespread font support
#				':D': '😃',
#				'^^': '😄',
#				'^_^':'😄',
#				':|': '😑',
				':(': '☹',
#				':/': '😕',
#				':\\':'😕',
#				'-.-':'😒',
#				':P' :'😛',
#				';P' :'😜',
#				'xP' :'😝',
#				';)' :'😉',
#				':?' :'😖',
#				'>:(':'😠',
#				'D:' :'😦',
#				':o' :'😯',
#				':O' :'😮',
#				'B)' :'😎'
				}
		for emoticon, uchar in emoticontable.items():
			if re.findall('(^|\W)'+re.escape(emoticon)+'(\W|$)', cmd) and random() < 0.333:
				reply('Did you mean {} (U+{:x}) with “{}”?'.format(uchar, ord(uchar), emoticon))
				break

		if cmd.startswith('open'):
			if '?' in cmd or '‽' in cmd:
				if cmd.count('?') >= 5:
					self.sendchan('afrabot: open?')
					return
				if self.lastopen:
					if self.spaceopen:
						reply('Space was last marked open on '+self.lastopen)
					else:
						reply('Space was last marked closed on '+self.lastopen)
				else:
					reply("I don't know when was the last time the space was open.")
			else:
				if cmd.count('!') > 5:
					reply('u mad bro?')
					return
				self.sendchan('Space is open!')
				self.lastopen = time.ctime()
				self.spaceopen = True
			return
		if cmd.startswith('closed'):
			if '?' in cmd or '‽' in cmd:
				if self.lastopen:
					if self.spaceopen:
						reply('Space was last marked open on '+self.lastopen)
					else:
						reply('Space was last marked closed on '+self.lastopen)
				else:
					reply("I don't know when was the last time the space was closed.")
			else:
				if cmd.count('!') > 5:
					reply('u mad bro?')
					return
				self.sendchan('Space is closed! Please remember to follow the shutdown protocol.')
				if target != self.channel:
					reply('Please remember to follow the shutdown protocol.')
				self.lastopen = time.ctime()
				self.spaceopen = False
			return
		if re.match('^ *genug +pleniert[.!]{,5}$', cmd) or re.match('^plenum[?!‽.]{,5}$', cmd):
			cs = self.chaossternchen
			if 'genug' in cmd:
				self.chaossternchen = []
				reply('Plenum beendet.')
			else:
				reply('Aye! So far, there are {} Chaos-☆'.format(len(cs)) + ('.' if len(cs) == 0 else ':'))
			for entry in enumerate(cs):
				reply('Chaos-☆ {}: {}'.format(*entry))
			return
		csmatch = re.match('^ *(delete|remove) +chaos-?([☆★☼☀*]|sternchen) *([0-9]+)[.!]{,5}$', cmd)
		if csmatch:
			try:
				num = int(csmatch.group(3))
				del self.chaossternchen[num]
				reply('Chaos-☆ {} deleted.'.format(num))
			except:
				reply('wut?')
			return
		if re.match('^help[?!‽.]*$', cmd):
			helptext = """open|closed? - query whether space is open
open|closed - set space open/closed
chaos*: [foobar] - add plenum topic
delete chaos* [num] - delete plenum topic number [n]
shutdown - list things to do when closing the space
plenum - list plenum topics
... and many more, doc urgently needed. Please submit PRs on github: https://github.com/afra/afrab0t
"""
			for line in helptext.splitlines():
				reply(line)
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
				reply(line)
			return
		if cmd == 'ponies?':
			reply('yes please!')
			return
		if re.match('^ *tell +afrab[o0]t +', cmd):
			reply('what is your problem?')
			return
		if cmd.rstrip('?') in ('where', 'location', 'wo'):
			reply('AfRA e.V. is located at Herzbergstr. 55, 10365 Berlin, 2.HH/Aufgang B, 3. floor on the'
					'left (Rm 3.08). Public transport: Tram M8, 21, 37 & Bus 256, N56, N50 → Herzbergstr./Siegfriedstr.'
					'Door closed? Try +49-176-29769254 !')
			return
		if cmd.rstrip('?') in ('tel', 'telefon', 'telephone', 'phone', 'handy', 'fon'):
			reply("Locked out? Wanna know what's up at AfRA? Try +49-176-29769254 !")
			return
		if cmd.rstrip('?!.') in ('cats', 'katzen', 'kittens', 'kätzchen'):
			try:
				submissions = self.reddit.get_subreddit('cats').get_hot(limit=50)
				index, item = next((i,s) for i,s in enumerate(submissions) if s.url not in self.catpiccache and not s.stickied and not s.is_self)
				self.catpiccache.append(item.url)
				if index != 5:
					reply('Got some cats for you: '+item.url)
				else:
					reply("Gee, you really like those cat things, don't you? You know, I could use some love, too: https://github.com/afra/afrab0t")
			except StopIteration:
				reply('The intertubes are empty.')
			return
		if cmd.rstrip('?!.') in ('answer', 'antworte', 'antwort'):
			reply('42')
			return
		# ETA handling
		if cmd.rstrip('?') in ('etas', 'who', 'da'):
			with self.db as db:
				db.execute("DELETE FROM etas WHERE timestamp < DATETIME('now', '-1 day')")
			etas = ', '.join(nick+': '+eta for nick,eta in db.execute("SELECT nick, eta FROM etas").fetchall())
			if etas:
				reply('Current ETAs: '+etas)
			else:
				reply('No ETAs have been announced yet.')
			return
		# key handling
		keycmd = re.match('key ([\w]+) to ([\w]+)( *: *.*)?', cmd)
		if keycmd:
			with self.db as db:
				keystate, = db.execute("SELECT keystate FROM keylog ORDER BY timestamp DESC LIMIT 1").fetchone()
				keystatelist = keystate.split(', ')
				fromnick, tonick, comment = keycmd.groups()
				if not fromnick in keystatelist:
					reply('According to my information, as of now {} does not have a key. Current key'
							'holders are {}.'.format(fromnick, keystate))
					return
				keystatelist[keystatelist.index(fromnick)] = tonick
				keystate = ', '.join(keystatelist)
				db.execute("INSERT INTO keylog VALUES (DATETIME('now'),?,?,?,?)", (fromnick, tonick, keystate, comment))
				self.sendchan('Key transfer: {}→{}. Current key holders: {}'.format(fromnick, tonick, keystate))
			return
		if cmd.rstrip('?') == 'progress':
			t = datetime.datetime.now().time()
			p = 0
			if t.hour > 6 and t.hour < 18:
				p = ((t.hour-6)*3600+t.minute*60+t.second)/(3600*11)
			foo = round(67*p)
			bar = '='*foo
			space = ' '*(67-foo)
			reply('['+bar+'>'+space+'] ({:.2f}%)'.format(p*100))
			return
		if cmd.startswith('keystate '):
			keystate = re.split('[,;/: ]*', cmd)[1:]
			self.db.execute("INSERT INTO keylog VALUES (DATETIME('now'),'','',?,'')", (', '.join(keystate),))
			self.sendchan('Key status set. Current key holders: {}'.format(', '.join(keystate)))
			return
		keylog = re.match('keylog *([0-9]*)', cmd)
		if keylog:
			num = max(50, int(keylog.group(1) or 8))
			dm('The latest {} key log entries:'.format(num))
			loglines = self.db.execute("SELECT * FROM keylog ORDER BY timestamp DESC LIMIT ?", (num,))
			for timestamp, fromnick, tonick, keystate, comment in reversed(loglines):
				dm('{}: {}→{}; Key holders {}; Comment: "{}"'.format(
						timestamp, fromnick, tonick, keystate, comment))
			dm('EOL')
			return
		if cmd.startswith("fuck you"):
			reply('Fucking is entirely unnecessary: I can reproduce via copy-and-paste!')
			return
		if cmd.startswith("geh kacken"):
			reply('Command "kacken" not implemented. You are welcome to submit a pull request on github at https://github.com/afra/afrab0t')
			return
		# fall-through
		c.notice(nick, 'I don\'t know what you mean with "{}"'.format(cmd))

def main():
	db = sqlite3.connect('afrab0t.db')
	db.execute("CREATE TABLE IF NOT EXISTS keylog (timestamp TIMESTAMP, fromnick TEXT, tonick TEXT, keystate TEXT, comment TEXT)")
	db.execute("CREATE TABLE IF NOT EXISTS etas (timestamp TIMESTAMP, nick TEXT, eta TEXT)")

	bot = Afrabot(db, settings.CHANNEL, settings.NICK, settings.SERVER, settings.PORT)
	bot.start()

if __name__ == "__main__":
	main()
