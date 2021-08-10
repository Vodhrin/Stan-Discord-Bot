import discord
import random
import time
import asyncio
import youtube_dl
import os
from PIL import Image, ImageFilter, ImageFont, ImageDraw

from StanCombat import *
from StanLanguage import *

def commands_init(passed_client):
	global client
	client = passed_client

	global ydl
	ydl_opts = {
	"cookiefile":"cookies.txt",
	"outtmpl":"cache/%(id)s.%(ext)s",
	"format": "bestaudio/best",
	"postprocessors": [{
	"key": "FFmpegExtractAudio",
	"preferredcodec": "mp3",
	"preferredquality": "192"
	}]}

	ydl = youtube_dl.YoutubeDL(ydl_opts)

async def cmd_disconnect(message):
	for voice_client in client.voice_clients:
		if voice_client.guild is message.author.guild:
			await voice_client.disconnect()
			print("Disconnected from voice channel " + voice_client.channel.name)

async def cmd_purge(message):
	if message.channel.permissions_for(message.guild.me).manage_messages:
		await message.channel.purge(limit=10, check=is_me)
		print(message.channel.name + " in the guild " + message.guild.name + " has been purged")

async def cmd_mass_purge():
	for guild in client.guilds:
		for channel in guild.text_channels:
			if channel.permissions_for(guild.me).manage_messages:
				await channel.purge(limit=10, check=is_me)
				print(channel.name + " in the guild " + guild.name + " has been purged")

async def cmd_attempt_combat(message, messages_instigate, messages_delete, flags):
	if not message.channel.permissions_for(message.guild.me).manage_messages:

		if message.channel.permissions_for(message.guild.me).send_messages:
			return

		await message.channel.send("I can't do that here, retard.")
		return

	if len(message.content.split()) < 3:
		return

	if message.channel not in flags:
		flags[message.channel] = False

	if flags[message.channel]:
		messages_delete.append(message)
		return

	current_attackers = []
	for i in messages_instigate:
		current_attackers.append(i.author)

	if message.author in current_attackers:
		messages_delete.append(message)
		return

	await message.channel.trigger_typing()
	messages_instigate.append(message)
	
async def cmd_sussify(message):
	text = advanced_auto_text_replace(clean_message(message))
	await message.channel.send(text)

async def cmd_niggerfy(message):
	new_content = replace_text_by_pos_tag(message.content, "nigger", "NN", "NNP")
	new_content = replace_text_by_pos_tag(new_content, "niggers", "NNS", "NNPS")
	await message.channel.send(new_content)

async def cmd_convert_to_int(message):
	comps = message.content.split()

	del comps[0:2]

	text = " ".join(comps)

	await message.channel.send(str(int.from_bytes(text.encode(), "little"))[0:2])

async def cmd_play_youtube_link(message):

	member = message.author
	text_channel = message.channel
	voice_channel = None
	if member.voice == None or member.voice.channel == None:
		await text_channel.send("Join a voice channel first, fagola.")
		return
	else:
		voice_channel = member.voice.channel

	link = message.content.split()[2]

	shortened = False
	if not link.startswith("https://www.youtube.com/watch"):
		if not link.startswith("https://youtu.be/"):
			await text_channel.send("Give me an actual link retard")
			return
		else:
			shortened = True

	already_connected = False
	for i in client.voice_clients:
		if i.channel == voice_channel:
			already_connected = True

	if not already_connected:
		await voice_channel.connect()

	voice_client = None
	for i in client.voice_clients:
		if i.channel == voice_channel:
			voice_client = i

	if voice_client == None:
		await text_channel.send("I shit myself")
		return

	loop = asyncio.get_event_loop()
	method = ydl.download
	args = [link]
	await loop.run_in_executor(None, method, args)
	filename = ""
	if not shortened:
		filename = "cache/" + link.split("=")[1].strip() + ".mp3"
	else: 
		filename = "cache/" + link.split("/")[3].strip() + ".mp3"

	if not os.path.isfile(filename):
		await text_channel.send("I shit myself")
		return

	audio = discord.FFmpegPCMAudio(filename)
	voice_client.play(audio)

def clean_message(message):
	words = message.content.split(" ")
	del words[0:2]
	return " ".join(words)

def is_me(m):
	
    return m.author == client.user