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
from discord.ext import tasks
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from PIL.ImageColor import getrgb

TOKEN = open("token.txt","r").readline()

intents = discord.Intents.default()
intents.members = True
intents.messages = True

client = discord.Client(intents = intents)
nlp = spacy.load("en_core_web_lg")

messages_to_delete = []
message_combat_bodies = []

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

	#ignore channels with no permissions
	if not message.channel.permissions_for(message.channel.guild.me).send_messages:
		return

	#respond to mentions
	if client.user.mentioned_in(message):
		adjectives = open("text/components/adjectives.txt", "r").readlines()
		nouns = open("text/components/nouns_singular.txt", "r").readlines()
		addons = open("text/components/addons_singular.txt", "r").readlines()

		adjective = ""
		if random.randrange(0, 2) == 0:
			adjective = adjectives[random.randrange(len(adjectives))]
			adjective = adjective.strip() + " "

		noun = nouns[random.randrange(len(nouns))].strip()

		addon = ""
		if random.randrange(0, 2) == 0:
			addon = addons[random.randrange(len(addons))]
			addon = " " + addon.strip()

		response = adjective + noun + addon
		await message.channel.send(response)
		return

	#test
	if message.content.startswith("!test"):
		filename = "cache/" + hashlib.md5(message.jump_url.encode()).hexdigest() + ".png"
		image = await create_combat_image()
		image.save(filename)
		await message.channel.send(file=discord.File(filename, "rapedbystan.png"))
		os.remove(filename)

	#stan fight
	if message.content.startswith("!fight") or message.content.startswith("!attack"):
		await message_combat(message)
		return

	#disconnect from voice command
	if message.content.startswith("!disconnectstan") and message.author.name == "Vodhr":
		for voice_client in client.voice_clients:
			if voice_client.guild is message.author.guild:
				await voice_client.disconnect()
				print("Disconnected from voice channel " + voice_client.channel.name)
				return

	#clean command
	if message.content.startswith("!cleanstanshittery"):
		for guild in client.guilds:
			for channel in guild.text_channels:
				if channel.permissions_for(guild.me).manage_messages:
					await channel.purge(limit=10, check=is_me)
					print(channel.name + " in the guild " + guild.name + " has been purged")
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
		if random.randrange(0, 251) == 1:
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
				new_message = await guild.system_channel.send(message)
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

			new_message = await channel.send(story)
			messages_to_delete.append(new_message)
			return

@tasks.loop(seconds = 60)
async def periodic_voice_action():

	for voice_client in client.voice_clients:
		await voice_client.disconnect()

	for guild in client.guilds:
		for channel in guild.voice_channels:
			if len(channel.members) > 0:

				if random.randrange(0, 76) == 1:
					await channel.connect()
					filenames = get_cum_filenames()
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

def replace_text_by_pos_tag(text, replacement, *tags):
	doc = nlp(text)
	new_text = ""

	for token in doc:
		new_word = token.text

		if token.tag_ in tags:
			if token.is_title:
				new_word = replacement.capitalize()
			else:
				new_word = replacement.lower()
		new_text += new_word
		new_text += token.whitespace_

	return new_text

def replace_text_tags(text):
	adjectives = open("text/components/adjectives.txt", "r").readlines()
	adjectives_afflication = open("text/components/adjectives_affliction.txt", "r").readlines()
	adverbs = open("text/components/adverbs.txt", "r").readlines()
	addons_singular = open("text/components/addons_singular.txt", "r").readlines()
	addons_plural = open("text/components/addons_plural.txt", "r").readlines()
	nouns_singular = open("text/components/nouns_singular.txt", "r").readlines()
	nouns_plural = open("text/components/nouns_plural.txt", "r").readlines()
	nouns_bodyparts = open("text/components/nouns_bodyparts.txt", "r").readlines()
	nouns_places_proper = open("text/components/nouns_places_proper.txt", "r").readlines()
	nouns_places_vague = open("text/components/nouns_places_vague.txt", "r").readlines()
	nouns_names_full = open("text/components/nouns_names_full.txt", "r").readlines()
	nouns_names_first_male = open("text/components/nouns_names_first_male.txt", "r").readlines()
	nouns_names_first_female = open("text/components/nouns_names_first_female.txt", "r").readlines()
	nouns_names_last = open("text/components/nouns_names_last.txt", "r").readlines()
	verbs_past = open("text/components/verbs_past.txt", "r").readlines()
	verbs_present = open("text/components/verbs_present.txt", "r").readlines()
	verbs_future = open("text/components/verbs_future.txt", "r").readlines()

	capitalization_flag = False
	if text.find("<") == 0:
		capitalization_flag = True

	new_text = text

	while "<a>" in new_text:
		word = adjectives[random.randrange(len(adjectives))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<a>", word, 1)

	while "<aa>" in new_text:
		word = adjectives_afflication[random.randrange(len(adjectives_afflication))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<aa>", word, 1)

	while "<ad>" in new_text:
		word = adverbs[random.randrange(len(adverbs))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<ad>", word, 1)

	while "<adds>" in new_text:
		word = addons_singular[random.randrange(len(addons_singular))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<adds>", word, 1)

	while "<addp>" in new_text:
		word = addons_plural[random.randrange(len(addons_plural))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<addp>", word, 1)

	while "<addf>" in new_text:
		if random.randrange(0, 2) == 1:
			word = addons_singular[random.randrange(len(addons_singular))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<addf>", word, 1)
		else:
			word = addons_plural[random.randrange(len(addons_plural))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<addf>", word, 1)

	while "<ns>" in new_text:
		word = nouns_singular[random.randrange(len(nouns_singular))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<ns>", word, 1)

	while "<np>" in new_text:
		word = nouns_plural[random.randrange(len(nouns_plural))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<np>", word, 1)

	while "<nf>" in new_text:
		if random.randrange(0, 2) == 1:
			word = nouns_singular[random.randrange(len(nouns_singular))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nf>", word, 1)
		else:
			word = nouns_plural[random.randrange(len(nouns_plural))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nf>", word, 1)

	while "<nbp>" in new_text:
		word = nouns_bodyparts[random.randrange(len(nouns_bodyparts))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nbp>", word, 1)

	while "<nplp>" in new_text:
		word = nouns_places_proper[random.randrange(len(nouns_places_proper))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nplp>", word, 1)		

	while "<nplv>" in new_text:
		word = nouns_places_vague[random.randrange(len(nouns_places_vague))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nplv>", word, 1)

	while "<nnf>" in new_text:
		word = nouns_names_full[random.randrange(len(nouns_names_full))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnf>", word, 1)

	while "<nnfm>" in new_text:
		word = nouns_names_first_male[random.randrange(len(nouns_names_first_male))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnfm>", word, 1)

	while "<nnff>" in new_text:
		word = nouns_names_first_female[random.randrange(len(nouns_names_first_female))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnff>", word, 1)

	while "<nnffl>" in new_text:
		if random.randrange(0, 2) == 1:
			word = nouns_names_first_male[random.randrange(len(nouns_names_first_male))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nnffl>", word, 1)
		else:
			word = nouns_names_first_female[random.randrange(len(nouns_names_first_female))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nnffl>", word, 1)

	while "<nnl>" in new_text:
		word = nouns_names_last[random.randrange(len(nouns_names_last))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnl>", word, 1)

	while "<vpa>" in new_text:
		word = verbs_past[random.randrange(len(verbs_past))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<vpa>", word, 1)

	while "<vpr>" in new_text:
		word = verbs_present[random.randrange(len(verbs_present))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<vpr>", word, 1)

	while "<vf>" in new_text:
		word = verbs_future[random.randrange(len(verbs_future))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<vf>", word, 1)

	while "<random>" in new_text:
		new_text = new_text.replace("<random>", str(random.randrange(1, 1000)), 1)

	return new_text

def advanced_auto_text_replace(text):

	adjectives = open("text/components/adjectives.txt", "r").readlines()
	adverbs = open("text/components/adverbs.txt", "r").readlines()
	addons_singular = open("text/components/addons_singular.txt", "r").readlines()
	addons_plural = open("text/components/addons_plural.txt", "r").readlines()
	nouns_singular = open("text/components/nouns_singular.txt", "r").readlines()
	nouns_plural = open("text/components/nouns_plural.txt", "r").readlines()
	nouns_bodyparts = open("text/components/nouns_bodyparts.txt", "r").readlines()
	nouns_places_proper = open("text/components/nouns_places_proper.txt", "r").readlines()
	nouns_places_vague = open("text/components/nouns_places_vague.txt", "r").readlines()
	nouns_names_full = open("text/components/nouns_names_full.txt", "r").readlines()
	nouns_names_first_male = open("text/components/nouns_names_first_male.txt", "r").readlines()
	nouns_names_first_female = open("text/components/nouns_names_first_female.txt", "r").readlines()
	nouns_names_last = open("text/components/nouns_names_last.txt", "r").readlines()
	verbs_past = open("text/components/verbs_past.txt", "r").readlines()
	verbs_past_participle = open("text/components/verbs_past_participle.txt", "r").readlines()
	verbs_present = open("text/components/verbs_present.txt", "r").readlines()
	verbs_future = open("text/components/verbs_future.txt", "r").readlines()
	verbs_gerund = open("text/components/verbs_gerund.txt", "r").readlines()

	doc = nlp(text)

	new_text = ""

	for token in doc:
		new_word = token.text

		if token.tag_ == "NN" and not token.is_stop:
			new_word = nouns_singular[random.randrange(len(nouns_singular))].strip()

		if token.tag_ == "NNS" and not token.is_stop:
			new_word = nouns_plural[random.randrange(len(nouns_plural))].strip()

		if token.tag_ == "JJ" and  not token.is_stop:
			new_word = adjectives[random.randrange(len(adjectives))].strip()

		if token.tag_ == "VB" and not token.is_stop:
			new_word = verbs_present[random.randrange(len(verbs_present))].strip()

		if token.tag_ == "VBD" and not token.is_stop:
			new_word = verbs_past[random.randrange(len(verbs_past))].strip()

		if token.tag_ == "VBG" and not token.is_stop:
			new_word = verbs_gerund[random.randrange(len(verbs_gerund))].strip()

		if token.tag_ == "VBN" and not token.is_stop:
			new_word = verbs_past_participle[random.randrange(len(verbs_past_participle))].strip()

		if token.is_title:
			new_word = new_word.capitalize()

		new_text += new_word
		new_text += token.whitespace_

	return new_text

def is_me(m):
	
    return m.author == client.user

def get_cum_filenames():

	return os.listdir("audio/cum_lines")

async def message_combat(message):

	message_combat_body = None

	#starting fight
	if message.content.startswith("!fight"):
		already_fighting = False
		for i in message_combat_bodies:
			if i.channel is message.channel:
				already_fighting = True

		#dont start a fight in this channel if there is already one going on
		if already_fighting:
			await message.channel.send("We're already fighting, retarded faggot.")
			return
		#start fight by instantiating a new body and adding it to list of bodies
		else:
			message_combat_body = Message_Combat_Body(message.channel)
			message_combat_bodies.append(message_combat_body)
			await message.channel.send("Lets go, nigger.")
			return

	#attacking
	if message.content.startswith("!attack"):
		in_fight = False
		for i in message_combat_bodies:
			if i.channel is message.channel:
				message_combat_body = i
				in_fight = True

		#tell user to start a fight first
		if not in_fight:
			await message.channel.send("Start a fight first, retard.")
			return
		#actual attack code
		else:
			viable_body_parts = []

			#make a list of only currently living bodyparts
			for i in message_combat_body.body_parts:
				if i.state != Body_Part.states["Dead"]:
					viable_body_parts.append(i)

			#pick random bodypart
			body_part = viable_body_parts[random.randrange(len(viable_body_parts))]

			#pick random dmg
			damage = random.randrange(0, 50)

			#initial attack acknowledgement
			await message.channel.send("_You attacked Stan's " + body_part.name + " for " + str(damage) + " damage!_")
			await message.channel.trigger_typing()
			await asyncio.sleep(1.5)
			health_after_attack = body_part.damage_part(damage)

			#if body part is still alive
			if health_after_attack > 0:
				await message.channel.send("_Stan's " + body_part.name + " now has " + str(health_after_attack) + " health left!_")
				if random.randrange(0, 3) == 1:
					await message.channel.trigger_typing()
					await asyncio.sleep(0.25)

					#random chance to say bodypart has affliction
					if random.randrange(0, 2) == 1:
						text = "_Stan's " + body_part.name + " is now <aa>!_"
					else:
						text = "_Stan's " + body_part.name + " is now <aa> <ad>!_"
						await message.channel.send(replace_text_tags(text))
				return

			#if bodypart died
			else:
				dead_parts = body_part.die()

				#if only one bodypart died
				if len(dead_parts) == 1:
					await message.channel.send("_Stan's " + body_part.name + " is now " + body_part.change_state(Body_Part.states["Dead"]) + "!_")

				#if multiple died
				else:
					text = "_Stan's "
					counter = 1
					for i in dead_parts:
						if counter - len(dead_parts)  != 0:
							text += i.name + ", "
							i.change_state(Body_Part.states["Dead"])
							counter = counter + 1
						else: 
							text += i.name + " "
							i.change_state(Body_Part.states["Dead"])
					text += "are now " + Body_Part.states["Dead"] + "!_"
					await message.channel.send(text)

				#if stan's health is now below 500 he overall dies
				if message_combat_body.get_current_total_health() < 500:
					message_combat_body.die()
					await message.channel.send(replace_text_tags("_Stan has been vanquished! His <vpa> body now resembles a pile of <a> <np>!"))
					await message.channel.trigger_typing()
					await asyncio.sleep(1.5)
					await message.channel.send(replace_text_tags("**I will return, you <a> <ns> <adds>.**"))
					return

				#random chance to say gay shit when bodypart dies
				if random.randrange(0, 3) == 1:
					significant_part = dead_parts[random.randrange(len(dead_parts))]
					await message.channel.send("_Stan cries out!_")
					await asyncio.sleep(0.5)
					await message.channel.send(replace_text_tags("**Oh god, my " + significant_part.name + "! It looks like a <vpa> <a> <ns> now!**"))
					return

async def create_combat_image():

	image_background = Image.open("images/background.png").convert("RGBA")
	image_head = Image.open("images/stanface.png").convert("RGBA")
	image_torso = Image.open("images/body_parts/torso.png").convert("RGBA")
	image_arm_right = Image.open("images/body_parts/arm_right.png").convert("RGBA")
	image_arm_left = Image.open("images/body_parts/arm_left.png").convert("RGBA")
	image_fingers_right = Image.open("images/body_parts/fingers_right.png").convert("RGBA")
	image_fingers_left = Image.open("images/body_parts/fingers_left.png").convert("RGBA")
	image_leg_right = Image.open("images/body_parts/leg_right.png").convert("RGBA")
	image_leg_left = Image.open("images/body_parts/leg_left.png").convert("RGBA")
	image_toes_right = Image.open("images/body_parts/toes_right.png").convert("RGBA")
	image_toes_left = Image.open("images/body_parts/toes_left.png").convert("RGBA")
	image_penis = Image.open("images/body_parts/penis.png").convert("RGBA")
	image_testicles = Image.open("images/body_parts/testicles.png").convert("RGBA")
	image_healthbar = Image.open("images/healthbar/1.png").convert("RGBA")

	composite = image_background
	await add_body_image(composite, image_head, (512, 192), False)
	await add_body_image(composite, image_torso, (512, 448), True,getrgb("white"))
	await add_body_image(composite, image_arm_right, (352, 352), True, getrgb("white"))
	await add_body_image(composite, image_arm_left, (672, 352), True, getrgb("white"))
	await add_body_image(composite, image_fingers_right, (832, 352), True, getrgb("white"))
	await add_body_image(composite, image_fingers_left, (192, 352), True, getrgb("white"))
	await add_body_image(composite, image_leg_right, (640, 672), True, getrgb("white"))
	await add_body_image(composite, image_leg_left, (384, 672), True, getrgb("white"))
	await add_body_image(composite, image_toes_right, (672, 768), True, getrgb("white"))
	await add_body_image(composite, image_toes_left, (352, 768), True, getrgb("white"))
	await add_body_image(composite, image_penis, (512, 640), True, getrgb("white"))
	await add_body_image(composite, image_testicles, (512, 608), True, getrgb("white"))
	await add_body_image(composite, image_healthbar, (512, 896), False)

	return composite

async def add_body_image(image_background, image_addition, position, replace=False, color=getrgb("white")):
	image_offset = (round(image_addition.width/2), round(image_addition.height/2))
	new_image_data = []
	if replace:
		for i in image_addition.getdata():
			if i[3] > 0:
				new_image_data.append(color)
			else:
				new_image_data.append(i)
		image_addition.putdata(new_image_data)
	image_background.alpha_composite(image_addition, tuple(map(sub, position, image_offset)))

class Message_Combat_Body:
	def __init__(self, channel):
		self.channel = channel

		self.left_eye = Body_Part("left eye", 25)
		self.right_eye = Body_Part("left eye", 25)
		self.left_ear = Body_Part("left ear", 10)
		self.right_ear = Body_Part("right ear", 10)
		self.nose = Body_Part("nose", 15)
		self.teeth = Body_Part("teeth", 35)
		self.head = Body_Part("head", 100, [self.left_eye, self.right_eye, self.left_ear, self.right_ear, self.nose, self.teeth])
		self.left_fingers = Body_Part("left fingers", 15)
		self.left_hand = Body_Part("left hand", 50, [self.left_fingers])
		self.left_arm = Body_Part("left arm", 100, [self.left_hand])
		self.right_fingers = Body_Part("right fingers", 15)
		self.right_hand = Body_Part("right hand", 50, [self.right_fingers])
		self.right_arm = Body_Part("right arm", 100, [self.right_hand])
		self.left_toes = Body_Part("left toes", 15)
		self.left_foot = Body_Part("left foot", 50, [self.left_toes])
		self.left_leg = Body_Part("left leg", 100, [self.left_foot])
		self.right_toes = Body_Part("right toes", 15)
		self.right_foot = Body_Part("right foot", 50, [self.right_toes])
		self.right_leg = Body_Part("right leg", 100, [self.right_foot])
		self.left_ass_cheek = Body_Part("left ass cheek", 35)
		self.right_ass_cheek = Body_Part("right ass cheek", 35)
		self.pubic_hair = Body_Part("pubic hair", 15)
		self.penis = Body_Part("penis", 15)
		self.testicles = Body_Part("testicles", 15)
		self.torso = Body_Part("torso", 300, [self.head, self.left_arm, self.right_arm, self.left_leg, self.right_leg, self.left_ass_cheek, self.right_ass_cheek, self.pubic_hair, self.penis, self.testicles])

		self.body_parts = [self.left_eye, self.right_eye, self.left_ear, self.right_ear, self.nose, self.teeth, self.head, self.left_fingers, self.left_hand, self.left_arm, self. right_fingers, self.right_hand, self.right_arm, self.left_toes, self.left_foot, self.left_leg, self.right_toes, self.right_foot, self.right_leg, self.left_ass_cheek, self.right_ass_cheek, self.pubic_hair, self.penis, self.testicles, self.torso]


	def get_current_total_health(self):
		number = 0
		for i in self.body_parts:
			number += i.health
		return number

	def die(self):
		for i in self.body_parts:
			del i
		del self

class Body_Part:

	states = {"Alive":"healthy and functional", "Dead":"destroyed", "Damaged":"damaged"}

	def __init__(self, name, max_health, dependent_parts=[]):
		self.name = name
		self.max_health = max_health
		self.health = self.max_health
		self.dependent_parts = dependent_parts
		self.state = Body_Part.states["Alive"]

	def change_state(self, new_state):
		self.state = new_state
		return self.state

	def damage_part(self, damage):
		self.health = self.health - damage
		return self.health

	def heal_part(self, amount):
		self.health = self.health + amount
		if self.health > self.max_health:
			self.health = self.max_health
		return self.health

	def die(self):
		dead_parts = [self]
		self.change_state(Body_Part.states["Dead"])
		self.health = 0
		for i in self.dependent_parts:
			i.health = 0
			i.die()
			dead_parts.append(i)
		return dead_parts

periodic_voice_action.start()
periodic_text_action.start()
client.run(TOKEN)