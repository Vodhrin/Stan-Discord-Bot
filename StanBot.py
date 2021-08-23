import discord
import random
import time
import asyncio
import hashlib
import os
import spacy
import numpy
from operator import sub
from datetime import datetime
from mutagen.mp3 import MP3
from discord.ext import tasks, commands
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from PIL.ImageColor import getrgb

from Config import *
from StanLanguage import *
from StanCombat import *
from StanCommands import *
from StanTunes import *

lanuage_init()
combat_init()
tunes_init()

@client.event
async def on_ready():

	print('Logged in as {0.user}'.format(client))

@client.event
async def on_guild_join(guild):
	flag = True
	for channel in guild.text_channels:
		if "general" in channel.name and flag:
			messages = open("text/arrival_messages.txt", "r").readlines()
			flag = False
			await channel.send(messages[random.randrange(len(messages))])
	if flag:
		messages = open("text/arrival_messages.txt", "r").readlines()
		await guild.system_channel.send(messages[random.randrange(len(messages))])

@client.event
async def on_message(message):

	#ignore his own messages
	if message.author == client.user:
		return

	if message.content.startswith(prefix):
		await client.process_commands(message)
		return

	#handles dm if the message is a dm
	if isinstance(message.channel, discord.DMChannel):
		content = message.content
		attachments = message.attachments
		name = message.author.name
		time = message.created_at

		files = []
		for i in attachments:
			file = await i.to_file()
			files.append(file)

		dbinc_channel = None
		for i in range(0, 100):
			try:
				dbinc_channel = await client.fetch_channel(575207765832761344)
				break
			except:
				pass

		if dbinc_channel != None:
			await dbinc_channel.send(name + " has proclaimed:\n\n" + content, files=files)

		if len(content) > 0:
			new_content = replace_text_by_pos_tag(content, "nigger", "NN", "NNP")
			new_content = replace_text_by_pos_tag(new_content, "niggers", "NNS", "NNPS")

			await message.channel.send(new_content)

		return

	#ignore channels with no permissions
	if not message.channel.permissions_for(message.channel.guild.me).send_messages:
		return

	#respond to mentions
	if client.user.mentioned_in(message):

		response = ""

		if random.randrange(0, 2) == 1:
			response += "<a> "

		response += "<ns>"

		if random.randrange(0, 2) == 1:
			response += " <adds>"

		await message.channel.send(replace_text_tags(response))
		return

	#cum zone line completions
	text = check_for_cum(message.content)
	if text != "" and random.randrange(0, 2) == 1:
		await message.channel.send(text)
		return

	#respond to usage of word "stan"
	if ("stan" in message.content or "Stan" in message.content) and random.randrange(0, 2) == 1:
		responses = open("text/name_responses.txt", "r").readlines()
		await message.channel.send(responses[random.randrange(len(responses))])
		return

	#random chance to copycat attachments with edits
	if len(message.attachments) > 0:
		for attachment in message.attachments:
			if attachment.content_type in ["image/png", "image/jpeg"]:
				if random.randrange(0, 16) == 1:
					filename = "cache/" + hashlib.md5(attachment.url.encode()).hexdigest() + ".png"
					await attachment.save(filename)
					image = Image.open(filename)
					image = image.convert("RGBA")
					image_stan = Image.open("images/stanface.png")
					image_stan = image_stan.convert("RGBA")
					image_stan = image_stan.resize(image.size)
					image = Image.blend(image, image_stan, 0.75)
					font = ImageFont.truetype("fonts/KGRedHands.ttf", size=round(image.size[0]/9))
					draw = ImageDraw.Draw(image)
					x = image.size[0] * 0.5
					y = image.size[1] * 0.99
					captions = open("text/captions.txt", "r").readlines()
					draw.text((x, y), captions[random.randrange(len(captions))], fill="rgb(0, 0, 0)", font=font, anchor="ms")
					image.save(filename)
					await message.channel.send(file=discord.File(filename, "rapedbystan.png"))
					os.remove(filename)
					return

	#random chance to copycat user with advanced replacements
	if len(message.content) > 1 and not message.content.startswith("https") and random.randrange(0, 31) == 1:
		text = advanced_auto_text_replace(message.content)
		await message.channel.send(text)
		return

	#random chance to copycat user with basic replacements
	if len(message.content) > 1 and not message.content.startswith("https") and random.randrange(0, 21) == 1:
		text = replace_text_by_pos_tag(message.content, "nigger", "NN", "NNP")
		text = replace_text_by_pos_tag(text, "niggers", "NNS", "NNPS")
		await message.channel.send(text)
		return

	#random chance to say phrase after a message is sent
	if not message.content.startswith("https") and random.randrange(0, 21) == 1:
		await asyncio.sleep(random.randrange(3, 16))
		phrases = open("text/phrases.txt", "r").readlines()
		phrase = replace_text_tags(phrases[random.randrange(len(phrases))])
		await message.channel.send(phrase)
		return

@tasks.loop(seconds = 60)
async def periodic_text_action():

	for message in messages_to_delete:
		difference = datetime.utcnow() - message.created_at
		if difference.total_seconds() > 900 and random.randrange(0, 2) == 1:
			await message.delete()
			messages_to_delete.remove(message)
			print("message deleted successfully in " + message.channel.name)


	for guild in client.guilds:
		if random.randrange(0, 1001) == 1:
			flag = True
			viable_members = []
			for member in guild.members:
				if member.status != discord.Status.offline:
					viable_members.append(member)
			if len(viable_members) > 1:
				member = viable_members[random.randrange(len(viable_members))]
				messages = open("text/periodic_mention_messages.txt", "r").read().split("#")
				message = messages[random.randrange(len(messages))]
				message = replace_text_tags(message)
				message = message.replace("<mention>", member.mention)
				channel = guild.system_channel
				if channel == None or not channel.permissions_for(channel.guild.me).send_messages:
					viable_channels = []
					for i in guild.text_channels:
						if i.permissions_for(i.guild.me).send_messages and "announce" not in i.name:
							viable_channels.append(i)
					channel = random.choice(viable_channels)
				if not channel.permissions_for(channel.guild.me).send_messages:
					return
				new_message = await channel.send(message)
				messages_to_delete.append(new_message)
				return

		if random.randrange(0, 251) == 1:
			stories = open("text/stories.txt", "r").read().split("#")
			story = stories[random.randrange(len(stories))]
			story = replace_text_tags(story)

			viable_channels = []
			for channel in guild.text_channels:
				if channel.permissions_for(channel.guild.me).send_messages and "announce" not in channel.name:
					viable_channels.append(channel)
			channel = viable_channels[random.randrange(len(viable_channels))]
			if not channel.permissions_for(channel.guild.me).send_messages:
				return
			new_message = await channel.send(story)
			messages_to_delete.append(new_message)
			return

@tasks.loop(seconds = 60)
async def periodic_voice_action():

	for guild in client.guilds:
		for channel in guild.voice_channels:

			for i in client.voice_clients:
				if i.channel == channel:
					return

			if len(channel.members) > 0:

				#random sounds
				if random.randrange(0, 215) == 1:
					await channel.connect()
					filenames = os.listdir("audio/random") 
					filename = filenames[random.randrange(len(filenames))]
					audio = discord.FFmpegPCMAudio("audio/random/" + filename)
					audio_length_in_seconds = int(MP3("audio/random/" + filename).info.length)
					for voice_client in client.voice_clients:
			 			if voice_client.channel == channel:
			 				voice_client.play(audio)
			 				await asyncio.sleep(round(audio_length_in_seconds * 1.5))
			 				voice_client.stop()
			 				await voice_client.disconnect()
			 				return

				#cum zone sounds
				if random.randrange(0, 76) == 1:
					await channel.connect()
					filenames = os.listdir("audio/cum_lines") 
					filename = filenames[random.randrange(len(filenames))]
					audio = discord.FFmpegPCMAudio("audio/cum_lines/" + filename)
					audio_length_in_seconds = int(MP3("audio/cum_lines/" + filename).info.length)
					for voice_client in client.voice_clients:
			 			if voice_client.channel == channel:
			 				voice_client.play(audio)
			 				await asyncio.sleep(round(audio_length_in_seconds * 1.5))
			 				voice_client.stop()
			 				await voice_client.disconnect()
			 				return

			 	#fart sound
				if random.randrange(0, 46) == 1:
			 		await channel.connect()
			 		audio = discord.FFmpegPCMAudio("audio/fart.mp3")
			 		for voice_client in client.voice_clients:
			 			if voice_client.channel == channel:
			 				voice_client.play(audio)
			 				await asyncio.sleep(random.uniform(1.25, 3.5))
			 				voice_client.stop()
			 				await voice_client.disconnect()
			 				return

			 	#stan scream sound
				if random.randrange(0, 46) == 1:
			 		await channel.connect()
			 		audio = discord.FFmpegPCMAudio("audio/cody_scream.mp3", options="-ss " + str(random.uniform(0, 4)))
			 		for voice_client in client.voice_clients:
			 			if voice_client.channel == channel:
			 				voice_client.play(audio)
			 				await asyncio.sleep(random.uniform(0.75, 2.5))
			 				voice_client.stop()
			 				await voice_client.disconnect()
			 				return

periodic_voice_action.start()
periodic_text_action.start()
client.run(TOKEN1)