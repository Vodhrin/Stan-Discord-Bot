import discord
import random
import time
import queue
import asyncio
import discord
import youtube_dl
from datetime import datetime
from enum import Enum
from discord.ext import tasks

from Config import *
from StanLanguage import *

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

def tunes_init():
	global voice_players
	voice_players = {}

async def tunes_query(ctx, url):

	user = ctx.author
	guild = ctx.guild
	voice_channel = user.voice.channel

	if voice_channel == None:
		return

	voice_player = None
	if voice_channel.id in voice_players:
		voice_player = voice_players[voice_channel.id]
	else:
		voice_client = None
		for i in client.voice_clients:
			if i.channel == voice_channel:
				voice_client = i

		if voice_client == None:
			try:				
				voice_client = await voice_channel.connect()
			except:
				return

		voice_player = VoicePlayer(voice_client)
		voice_players[voice_channel.id] = voice_player

	song = await YTDLSource.from_url(url, stream=True)

	voice_player.add_song(song)

class YTDLSource(discord.PCMVolumeTransformer):

	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)

		self.data = data

		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]

		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class VoicePlayer:
	def __init__(self, voice_client):
		if voice_client == None:
			return
		self.voice_client = voice_client
		self.channel = voice_client.channel
		self.songs = queue.Queue()
		self.loop = False
		self.initialized = False
		self.end.start()

	@tasks.loop(seconds = 30)
	async def end(self):
		if self.initialized and self.voice_client and not self.voice_client.is_playing():
			await self.voice_client.disconnect()

		elif self.voice_client == None:
			self.delete()

	def play_next(self):
		song = None
		try:
			song = self.songs.get(block=False)
		except:
			self.delete()
			return

		if self.loop:
			self.add_song(song)

		self.play_song(song)

	def add_song(self, song):

		self.songs.put(song, block=False)

		if not self.initialized:
			self.initialized = True
			self.play_next()

	def play_song(self, song):
		if self.voice_client != None:
			self.voice_client.play(song, after=self.on_end)
		else:
			self.delete()

	def on_end(self, error):

		self.play_next()

	def delete(self):
		if voice_players[self.channel.id] == self:
			del voice_players[self.channel.id]

		del self

