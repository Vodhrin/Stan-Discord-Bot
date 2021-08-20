import discord
import random
import time
import asyncio
import youtube_dl
import os
from PIL import Image, ImageFilter, ImageFont, ImageDraw

from StanCombat import *
from StanLanguage import *
from StanTunes import *

def commands_init(passed_client):
	global client
	client = passed_client

async def cmd_disconnect(message):
	for i in client.voice_clients:
		if i.guild is message.author.guild:
			await i.disconnect()
			i.cleanup()
			print("Disconnected from voice channel " + i.channel.name)

async def cmd_mass_disconnect(message):
	for i in client.voice_clients:
		await i.disconnect()
		i.cleanup()
		print("Disconnected from voice channel " + i.channel.name)

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

	if len(message.content.split()) < 3:
		return

	await tunes_query(message)



def clean_message(message):
	words = message.content.split(" ")
	del words[0:2]
	return " ".join(words)

def is_me(m):
	
    return m.author == client.user