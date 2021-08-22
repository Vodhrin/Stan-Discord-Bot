import discord
import random
import time
import asyncio
import hashlib
import os
import youtube_dl
import numpy
import math
import pickle
from enum import Enum
from discord.ext import tasks

from Config import *
from StanLanguage import *

def tunes_init():
	global voice_players
	global songs
	voice_players = []
	songs = []

	global ydl
	global yi
	ydl_opts = {
	"cookiefile":"cookies.txt",
	"outtmpl":"cache/%(id)s.%(ext)s",
	"format": "bestaudio/best",
	"postprocessors": [{
	"key": "FFmpegExtractAudio",
	"preferredcodec": "mp3",
	"preferredquality": "192"
	}]}
	yi_opts = {
	"cookiefile":"cookies.txt",
	}

	ydl = youtube_dl.YoutubeDL(ydl_opts)
	yi = youtube_dl.YoutubeDL(yi_opts)

	loop_short.start()
	loop_long.start()

async def tunes_query(message):
	member = message.author
	text_channel = message.channel
	voice_channel = None
	voice_player = None
	infos = []
	songs_to_play = []
	already_playing = False
	loop = False

	#get the user who requested to play's voice channel and error if they arent in one
	if member.voice == None or member.voice.channel == None:
		await text_channel.send("Join a voice channel first, fagola.")
		return
	else:
		voice_channel = member.voice.channel

	link = message.content.split()[2]

	if link == "loop":
		loop = True

	if (not loop) and (not link.startswith("https://www.youtube.com/watch")) and (not link.startswith("https://youtu.be/")) and (not link.startswith("https://www.youtube.com/playlist")):
		await text_channel.send("Give me an actual link, retard.")
		return

	#check if stan is already connected to the user's channel
	already_connected = False
	for i in client.voice_clients:
		if i.channel == voice_channel:
			already_connected = True

	#connect to the user's voice channel if stan wasn't connected
	if not already_connected:
		await voice_channel.connect()

	#get the voice client corresponding to the user's voice channel
	voice_client = None
	for i in client.voice_clients:
		if i.channel == voice_channel:
			voice_client = i

	#if for some reason a voice client couldnt be found for the user's voice channel, then something fucked up above and stan errors
	if voice_client == None:
		await text_channel.send("I shit myself")
		return

	await message.channel.trigger_typing()

	for i in voice_players:
		if i.voice_client == voice_client:
			voice_player = i
			if voice_player.is_playing():
				already_playing = True
			break

	if voice_player == None:
		voice_player = Voice_Player(voice_client)
		voice_players.append(voice_player)

	if loop:
		await tunes_loop(text_channel, voice_player)
		return

	info = yi.extract_info(link, download=False)

	if "entries" in info:
		for i in info["entries"]:
			if i not in infos:
				infos.append(i)
	else:
		if info not in infos:
			infos.append(info)

	for i in infos:
		for o in songs:
			if i["id"] == o.id:
				infos.remove(i)
				songs_to_play.append(o)
				voice_player.add_song(o)

	for i in infos:
		link = "https://www.youtube.com/watch?v=" + i["id"]
		loop = asyncio.get_event_loop()
		method = ydl.download
		args = [link]
		await loop.run_in_executor(None, method, args)
		new_song = Song(i)
		songs_to_play.append(new_song)
		voice_player.add_song(new_song)

	if not already_playing:
		await echo_songs(message.channel, songs_to_play, False)
	else:
		await echo_songs(message.channel, songs_to_play, True)

async def tunes_loop(text_channel, voice_player):

	if len(voice_player.songs) < 1 or not voice_player.is_playing():
		await text_channel.send("Loop what faggot.")
		return

	voice_player.toggle_loop()

	await text_channel.send("Looping...")

async def echo_songs(channel, songs, queued=False):
	names = []
	for i in songs:
		names.append(i.name)

	composite = get_composite_noun(names)

	if queued:
		await channel.send("Queued: " + composite + ".")
	else:
		await channel.send("Playing: " + composite + ".")

@tasks.loop(seconds = 60)
async def loop_short():

	for i in voice_players:
		if not i.is_playing() and not i.paused:
			disconnected = False
			while not disconnected:
				try:
					if i.voice_client == None:
						break
					await i.voice_client.disconnect()
					disconnected = True
				except:
					pass

@tasks.loop(seconds = 600)
async def loop_long():

	all_current_songs = []
	for i in voice_players:
		all_current_songs.extend(i.songs)

	for i in songs:
		if i not in all_current_songs:
			i.remove()

class Voice_Player():
	def __init__(self, voice_client):
		self.voice_client = voice_client
		if voice_client == None:
			del self
			return
		self.songs = songs
		self.paused = False
		self.loop = False
		self.current_song = None

	def play_next(self):
		if self.voice_client == None:
			self.remove()
			return

		if not self.loop:
			self.current_song = self.songs[0]
			if self.current_song != None:
				self.voice_client.play(self.current_song.audio, after=self.audio_ended)
			self.songs.remove(self.current_song)
		else:
			if self.current_song != None:
				self.songs.append(self.current_song)
			self.current_song = self.songs[0]
			if self.current_song != None:
				self.voice_client.play(self.current_song.audio, after=self.audio_ended)
			self.songs.remove(self.current_song)

	def audio_ended(self, error):
		if len(self.songs) < 1:
			return

		self.play_next()

	def add_song(self, song):
		if song:
			self.songs.append(song)

		if not self.is_playing() and not self.paused:
			self.play_next()

	def add_songs(self, songs):
		if songs:
			self.songs.extend(songs)

		if not self.is_playing() and not self.paused:
			self.play_next()

	def toggle_loop(self):
		if self.loop:
			self.loop = False
		else:
			self.loop = True

	def is_playing(self):
		if self.voice_client.is_playing():
			return True
		return False

	def remove(self):
		voice_players.remove(self)
		del self

class Song():
	def __init__(self, info):
		self.id = info["id"]
		self.name = info["title"]
		self.filename = "cache/" + self.id + ".mp3"

		if not os.path.isfile(self.filename):
			del self
			return

		self.audio = discord.FFmpegPCMAudio(self.filename)
		songs.append(self)


	def remove(self):
		os.remove(self.filename)
		songs.remove(self)
		del self
