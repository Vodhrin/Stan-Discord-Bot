import discord
import random
import time
import asyncio
import hashlib
import os
import numpy
import math
import persistent
import transaction
import ZODB, ZODB.FileStorage
import BTrees.OOBTree
from enum import Enum
from datetime import datetime
from discord.ext import tasks
from operator import sub
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from PIL.ImageColor import getrgb

from Config import *
from StanLanguage import *

def combat_init():

	# players and stans are lists of all of the current player combatants and stan combatants involved in combat in any channel
	# there is only one stan per channel at a time, but players are persistent across all channels
	# stans are created when combat starts in a channel which has previously not had it, players are created in the first channel they start combat in and persist until the script ends (for now)

	# handlers and responders are dictionaries where the key is the channel that they correspond to
	# handlers handle all incoming +combat commands from specific channels
	# responders handle all outgoing messages to specific channels
	# dm messages are not handled by the responder, but instead by the player class corresponding to that user

	# counters and channels_active are dictionaries that assist the responder and handler logic, the key is also the channel that they correspond to
	# counters is used to prevent excessive recursion of the request handers
	# because request handlers recursively check for more messages every 5 seconds, they would essentially continue checking forever if there was no counter
	# therefore, the counter checks how many recursive loops the handler in that channel has gone through, if this goes above 10, the channel is assumed inactive
	# inactive channels have their value set to false in the channels_active dictionary and the handler for that channel stops recursing
	# when a new query comes to a channel marked inactive, the query function detects it and resets the handler so that it begins recursing again, and the loop continues
	# this is all to prevent excessive recursion while still maintaining snappy (5 second) response time to requests

	# recent_messages is a dictionary with a channel as key and a list of messages as value which just tracks the most recent messages sent by the responder
	# the only purpose of this is so that the most recent messages dont get deleted by the responder so that the recent combat update is still there if you take a short break

	global players
	global stans
	global handlers
	global responders
	global counters
	global channels_active
	global recent_messages
	global db
	global dbm
	players = []
	stans = []
	handlers = {}
	responders = {}
	counters = {}
	channels_active = {}
	recent_messages = {}

	storage = ZODB.FileStorage.FileStorage("combat_data/database.fs")
	db = ZODB.DB(storage)
	dbm = DatabaseManager()

async def query(channel, message):

	if channel not in handlers:
		responders[channel] = Responder(channel)
		handlers[channel] = RequestHandler(channel)
		channels_active[channel] = True
		recent_messages[channel] = []
		handlers[channel].add_message(message)
		await handlers[channel].wait_for_more_messages()
		return
	elif channels_active[channel] == False:
		channels_active[channel] = True
		handlers[channel].add_message(message)
		await handlers[channel].wait_for_more_messages()

	handlers[channel].add_message(message)

class RequestHandler:
	def __init__(self, channel):
		self.channel = channel
		self.messages = []
		self.responder = responders[self.channel]
		counters[self.channel] = 0

	def add_message(self, message):
		self.messages.append(message)
		responders[self.channel].messages.append(message)

	async def wait_for_more_messages(self):
		before_amount = len(self.messages)
		await asyncio.sleep(5)
		#if no new messages have been added and self.messages is not empty
		if before_amount == len(self.messages) and self.messages:
			cm = await CombatManager.create(self.channel, self.messages)
			self.messages = []
			if cm != None:
				await self.responder.respond(cm.response)
				for i in cm.dm_responses:
					await self.responder.respond_dm(i)
			counters[self.channel] = 0
			await self.wait_for_more_messages()
		elif self.messages:
			counters[self.channel] = 0
			await self.wait_for_more_messages()
		else:
			if counters[self.channel] >= 10:
				channels_active[self.channel] = False
				return
			counters[self.channel] += 1
			await self.wait_for_more_messages()

class Responder:
	def __init__(self, channel):
		self.channel = channel
		self.image_filename = "cache/" + str(self.channel.id) + ".png"
		self.log_filename = "cache/" + str(self.channel.id) + ".txt"
		self.log = ""
		self.messages = []

		self.delete_messages.start()

	def cache_image(self, image):
		image.save(self.image_filename)
		return discord.File(self.image_filename, "rapedbystan.png")

	def cache_log(self):
		file = open(self.log_filename, "w")
		try:
			file.write(self.log)
		except:
			file.close()
			return None
		file.close()
		return discord.File(self.log_filename, "combatlog.txt")

	def clear_cache(self):
		try:
			os.remove(self.image_filename)
		except:
			pass
		try:
			os.remove(self.log_filename)
		except:
			pass

	def clear_log(self):
		self.log = ""

	@tasks.loop(seconds=10.0)
	async def delete_messages(self):
		for i in self.messages:
			if i in recent_messages[i.channel]:
				continue
			difference = datetime.utcnow() - i.created_at
			if difference.total_seconds() > 30:
				try:
					await i.delete()
					self.messages.remove(i)
				except:
					pass

	async def send_message(self, content=None, file=None, delete=True):
		if (content == None or content == "") and file == None:
			return
		new_message = await self.channel.send(content=content, file=file)

		if len(recent_messages[self.channel]) < 2:
			recent_messages[self.channel].append(new_message)
		elif len(recent_messages[self.channel]) == 2:
			recent_messages[self.channel].pop(0)
			recent_messages[self.channel].append(new_message)
		else:
			difference = len(recent_messages[self.channel]) - 3

			for i in range(difference):
				recent_messages[self.channel].pop(0)

			recent_messages[self.channel].append(new_message)

		if delete:
			self.messages.append(new_message)

	async def respond(self, response):
		image_file = self.cache_image(response.image)
		log_file = None
		new_log_text = response.text
		new_log_text = new_log_text.replace("_", "")
		new_log_text = new_log_text.replace("**", "")
		self.log += new_log_text + "\n"
		if response.stan_killed:
			log_file = self.cache_log()
			self.clear_log()
		await self.send_message(file=image_file)
		await self.send_message(content=response.text, file=log_file)
		try:
			await self.send_message(file=log_file, delete=False)
		except:
			pass
		self.clear_cache()

	async def respond_dm(self, response):
		image_file = self.cache_image(response.image)
		await response.player.dm_user(file=image_file)
		await response.player.dm_user(content=response.text)
		self.clear_cache()

class Response:
	def __init__(self, image, text, stan_killed, player=None):
		self.image = image
		self.text = text
		self.stan_killed = stan_killed
		self.player = player

class CombatManager:
	@classmethod
	async def create(cls, channel, messages):
		self = CombatManager()
		self.channel = channel
		self.messages = messages
		self.responder = responders[self.channel]

		self.image_generator = ImageGenerator()

		self.stan = self.get_stan(stans, channel)
		self.player_infos = self.get_player_infos(players, messages)

		#remove dead players from players
		player_infos_clone = self.player_infos.copy()
		for i in player_infos_clone:
			if i.body.state == State.DEAD:
				user_image = await self.image_generator.generate(i.body)
				percent = math.ceil(i.body.injury_multiplier * 100)
				text = ""
				text += "_**You are currently dead with " + str(percent) + "%" + " health left.**_\n_Your health will regenerate over time and your chance to revive increases as your healthpool increases._"
				new_response = Response(user_image, text, False, i)
				await self.responder.respond_dm(new_response)
				del self.player_infos[i]

		if len(self.player_infos) < 1:
			return None

		self.player_names = {}
		for i in self.player_infos:
			name = await i.get_name()
			self.player_names[i] = name

		self.attacks = []
		self.player_attacks = []
		self.stan_attacks = []
		self.retaliation_dict = {}

		for i in self.player_infos:
			new_attack = Attack(i, self.stan, self.player_infos[i])
			self.attacks.append(new_attack)
			self.player_attacks.append(new_attack)
			self.retaliation_dict[i] = random.randrange(0, 5) == 1

		for i in self.retaliation_dict:
			if self.retaliation_dict[i]:
				new_attack = Attack(self.stan, i)
				self.attacks.append(new_attack)
				self.stan_attacks.append(new_attack)

		self.stan_killed = False
		if self.stan.body.get_current_total_health() < 500:
			self.stan_killed = True

		stan_image = await self.image_generator.generate(self.stan.body)
		message_text = self.generate_message()
		self.response = Response(stan_image, message_text, self.stan_killed)
		self.dm_responses = []
		for i in self.stan_attacks:
			message_text = self.generate_dm_message(i)
			user_image = await self.image_generator.generate(i.body_attacked)
			self.dm_responses.append(Response(user_image, message_text, False, i.combatant_attacked))

		if self.stan_killed:
			self.stan.die()

		return self

	def get_stan(self, stans, channel):
		for i in stans:
			if i.cid == channel.id:
				return i

		new_stan = Stan(channel.id)
		stans.append(new_stan)
		return new_stan

	def get_player(self, players, uid):
		for i in players:
			if i.uid == uid:
				return i

	def get_player_infos(self, players, messages):
		player_infos = {}
		for i in messages:

			weapon = i.content.replace("+combat", "").strip()

			add_flag = True
			for o in player_infos:
				if o.uid == i.author.id:
					add_flag = False
			if add_flag:
				added = False
				for o in players:
					if o.uid == i.author.id:
						player_infos[o] = weapon
						added = True
				if not added:
					new_player = Player(i.author.id, i.author.name)
					player_infos[new_player] = weapon
					players.append(new_player)
		return player_infos

	def get_players(self, players, messages):
		players_present = []
		for i in messages:
			add_flag = True
			for o in players_present:
				if o.uid == i.author.id:
					add_flag = False
			if add_flag:
				added = False
				for o in players:
					if o.uid == i.author.id:
						players_present.append(o)
						added = True
				if not added:
					new_player = Player(i.author.id)
					players_present.append(new_player)
					players.append(new_player)
		return players_present

	def generate_message(self):
		text = ""

		for i in self.player_attacks:
			attacked_part_names = []
			maybe_total = ""
			maybe_n = ""

			vowels = ["a", "e", "i", "o", "u"]

			if len(i.attacked_parts) > 1:
				maybe_total = " total"
			if i.weapon != "" and i.weapon[0] in vowels:
				maybe_n = "n"

			for o in i.attacked_parts:
				attacked_part_names.append(o.name)

			if i.weapon == "":
				text += "_" + self.player_names[i.combatant_attacker] + " attacked Stan's " + get_composite_noun(attacked_part_names) + " for " + str(i.damage) + maybe_total + " damage!_" + "\n"
			else:
				text += "_" + self.player_names[i.combatant_attacker] + " attacked Stan's " + get_composite_noun(attacked_part_names) + " with a" + maybe_n + " " + i.weapon +  " for " + str(i.damage) + maybe_total + " damage!_" + "\n"

		total_killed_parts = []
		for i in self.player_attacks:
			for o in i.killed_parts:
				if o not in total_killed_parts:
					total_killed_parts.append(o)

		total_damaged_parts = []
		for i in self.player_attacks:
			for o in i.attacked_parts:
				if (o not in total_damaged_parts) and (o not in total_killed_parts):
					total_damaged_parts.append(o)

		for i in total_damaged_parts: 
			text += "_Stan's " + i.name + " now has " + str(i.health) + " health left!_" + "\n"

			if random.randrange(0, 3) == 1:
				affliction_line = ""
				if random.randrange(0, 2) == 1:
					affliction_line = "**_Stan's " + i.name + " is now <aa>!_**"
				else:
					affliction_line = "**_Stan's " + i.name + " is now <ad> <aa>!_**"
				text += replace_text_tags(affliction_line) + "\n" 

		#dead parts
		if len(total_killed_parts) > 0:
			if len(total_killed_parts) == 1:
				text += "**_Stan's " + total_killed_parts[0].name + " is now destroyed!_**" + "\n"
			else:
				total_killed_parts_names = []
				for i in total_killed_parts:
					total_killed_parts_names.append(i.name)
				text += "**_Stan's " + get_composite_noun(total_killed_parts_names) + " are now destroyed!_**" + "\n"

			if random.randrange(0, 3) == 1:
				text += "_Stan cries out!_" + "\n"
				text += replace_text_tags("**Oh god, my " + random.choice(total_killed_parts).name + "! It looks like a <vpa> <a> <ns> now!**") + "\n"

		if len(self.stan_attacks) > 0:
			if not self.stan_killed:
				for i in self.retaliation_dict:
					retaliated_player_names = []
					for o in self.retaliation_dict:
						if self.retaliation_dict[o]:
							if o.name not in retaliated_player_names:
								retaliated_player_names.append(o.name)
				text += "**_Stan retaliated against " + get_composite_noun(retaliated_player_names) + "!_**" + "\n"

		if self.stan_killed:
			text += "\n"
			text += replace_text_tags("_Stan has been vanquished! His <vpa> body now resembles a pile of <a> <np>!_") + "\n"
			text += replace_text_tags("**I will return, you <a> <ns> <addp>.**") + "\n\n"

			sorted_damage_table = sorted(self.stan.damage_table.items(), key=lambda kv:kv[1], reverse=True)
			if len(sorted_damage_table) > 0:
				for idx, i in enumerate(sorted_damage_table):
					text += str(idx + 1) + ". " + sorted_damage_table[idx][0] + " --- " + str(sorted_damage_table[idx][1]) + " total damage" + "\n"

		return text

	def generate_dm_message(self, attack):
		text = ""

		vowels = ["a", "e", "i", "o", "u"]

		maybe_total = ""
		if len(attack.attacked_parts) > 1:
			maybe_total = "total "
		maybe_n = ""
		if attack.weapon[0] in vowels:
			maybe_n = "n"

		attacked_parts_names = []
		for i in attack.attacked_parts:
			if i.name not in attacked_parts_names:
				attacked_parts_names.append(i.name)

		if len(attack.attacked_parts) == 1:
			text += "_Stan attacked your " + attack.attacked_parts[0].name + " with a" + maybe_n + " " + attack.weapon + " for " + str(attack.damage) + " " + maybe_total +"damage!_" + "\n"
		else:
			text += "_Stan attacked your " + get_composite_noun(attacked_parts_names) + " with a" + maybe_n + " " + attack.weapon + " for " + str(attack.damage) + " " + maybe_total +"damage!_" + "\n"

		return text

class DatabaseManager:
	def __init__(self):
		connection = db.open()
		root = connection.root
		root.players = BTrees.OOBTree.BTree()
		root.stans = BTrees.OOBTree.BTree()
		transaction.commit()
		connection.close()

	def save_stan(self, stan):
		connection = db.open()
		root = connection.root
		root.stans[stan.cid] = stan
		transaction.commit()
		connection.close()

	def get_stan(self, cid):
		connection = db.open()
		root = connection.root

		if not root.stans.has_key(cid):
			connection.close()
			return None

		stan = root.stans[cid]
		connection.close()
		return stan

	def save_player(self, player):
		connection = db.open()
		root = connection.root
		root.players[player.uid] = player
		transaction.commit()
		connection.close()

	def get_player(self, uid):
		connection = db.open()
		root = connection.root
		
		if not root.stans.has_key(uid):
			connection.close()
			return None

		player = root.players[uid]
		connection.close()
		return player

class ImageGenerator:
	def __init__(self):
		self.image = None

	async def generate(self, body):

		image_background = Image.open("images/background.png").convert("RGBA")

		body_part_data = open("text/body_part_image_data.txt", "r").readlines()

		file_name = ""
		if body.get_current_total_health() > 501:
			mult = (body.get_current_total_health() - 500) / (body.max_health - 500)
			file_name = "images/healthbar/" + str(min(56 - round(mult * 55), 55)) + ".png"
		else:
			file_name  = "images/healthbar/55.png"

		image_healthbar = Image.open(file_name).convert("RGBA")

		composite = image_background

		for i in os.listdir("images/body_parts"):

			i_stripped = i.replace(".png", "")
			for o in body_part_data:
				if o.startswith(i_stripped):
					body_part = body.get(i_stripped)
					file_name = "images/body_parts/" + i
					image = Image.open(file_name).convert("RGBA")
					x,y = o.strip().split(":")[1].split(",")

					if body_part.is_alive():
						self.add_body_image(composite, image, (int(x), int(y)), self.get_color(body_part))

		if body.head.is_alive():
			if body.uid == 0:
				self.add_head_image(composite, "images/stanface.png", body)
			else:
				user = await client.fetch_user(body.uid)
				file_name = "cache/" + hashlib.md5(str(body.uid).encode()).hexdigest() + ".png"
				await user.avatar_url_as(format="png", static_format="png", size=256).save(file_name)

				image = Image.open(file_name).convert("RGBA")
				image = image.resize((256, 256))
				image_mask = Image.open("images/head_mask.png").convert("RGBA")
				image_empty = Image.open("images/empty_image.png").convert("RGBA")

				cropped = Image.composite(image, image_empty, image_mask)
				cropped.save(file_name)
				self.add_head_image(composite, file_name, body)
				os.remove(file_name)

		#add healthbar
		composite.alpha_composite(image_healthbar, tuple(map(sub, (512, 896), (round(image_healthbar.width/2), round(image_healthbar.height/2)))))

		self.image = composite
		return composite

	def add_body_image(self, image_background, image_addition, position, color=getrgb("white")):
		image_offset = (round(image_addition.width/2), round(image_addition.height/2))
		new_image_data = []
		for i in image_addition.getdata():
			if i[3] > 0:
				new_image_data.append(color)
			else:
				new_image_data.append(i)
		image_addition.putdata(new_image_data)
		image_background.alpha_composite(image_addition, tuple(map(sub, position, image_offset)))

	def weight_colors(self, color_1, color_2, weight_towards_color_1):

		w_1 = weight_towards_color_1
		w_2 = 1 - weight_towards_color_1

		x_1, x_2, x_3 = color_1
		z_1, z_2, z_3 = color_2

		return (round(x_1*w_1 + z_1*w_2), round(x_2*w_1 + z_2*w_2), round(x_3*w_1 + z_3*w_2))

	def get_color(self, body_part):

		color = self.weight_colors(getrgb("red"), getrgb("white"), 1 - body_part.health / body_part.max_health)
		return color

	def add_head_image(self, image_background, file_name, body):

		position = (512, 192)
		head = body.head
		image = Image.open(file_name).convert("RGBA")
		image_offset = (round(image.width/2), round(image.height/2))

		weight = head.health / head.max_health

		new_image_data = []

		for i in image.getdata():
				if i[3] > 0:
					x, y, z, a = i
					color_1 = (x, y, z)
					color_2 = getrgb("red")

					w_1 = weight
					w_2 = 1 - weight

					x_1, x_2, x_3 = color_1
					z_1, z_2, z_3 = color_2

					new_color = (round(x_1*w_1 + z_1*w_2), round(x_2*w_1 + z_2*w_2), round(x_3*w_1 + z_3*w_2))

					new_color_alpha = (new_color[0], new_color[1], new_color[2], i[3])

					new_image_data.append(new_color_alpha)
				else:
					new_image_data.append(i)
		image.putdata(new_image_data)
		image_background.alpha_composite(image, tuple(map(sub, position, image_offset)))

class State(Enum):
	DEAD = 0
	ALIVE = 1

class Body:
	def __init__(self, uid):
		self.eye_r = None
		self.eye_l = None
		self.ear_r = None
		self.ear_l = None
		self.nose = None
		self.teeth = None
		self.head = None
		self.fingers_r = None
		self.fingers_l = None
		self.hand_r = None
		self.hand_l = None
		self.arm_r = None
		self.arm_l = None
		self.nipple_r = None
		self.nipple_l = None
		self.toes_r = None
		self.toes_l = None
		self.foot_r = None
		self.foot_l = None
		self.leg_r = None
		self.leg_l = None
		self.ass_cheek_r = None
		self.ass_cheek_l = None
		self.anus = None
		self.pubic_hair = None
		self.penis = None
		self.testicles = None
		self.torso = None

		self.body_parts = []

		self.init_body_parts()

		self.max_health = self.get_current_total_health()

		self.state = State.ALIVE

		self.injury_multiplier = 1

		self.uid = uid

	def get(self, attrname):
		return getattr(self, attrname)

	def set(self, attrname, value):
		return setattr(self, attrname, value)

	def init_body_parts(self):

		infos = open("text/body_part_infos.txt", "r").readlines()
		dependencies = open("text/body_part_dependencies.txt", "r").readlines()
		relations = open("text/body_part_relations.txt", "r").readlines()

		#instantiate all of the parts with only names and health first
		for i in list(vars(self).keys())[0:28]:

			info = None

			for o in infos:
				if o.startswith(i):
					info = o.strip().split(":")[1]

			name = info.split(",")[0]
			health = int(info.split(",")[1])

			self.set(i, Body_Part(name, health))
			self.body_parts.append(self.get(i))

		for i in list(vars(self).keys())[0:28]:

			dependents = None
			relateds = None

			for o in dependencies:
				if o.startswith(i):
					dependents = o.strip().split(":")[1]

			for o in relations:
				if o.startswith(i):
					relateds = o.strip().split(":")[1]

			dependent_parts = []
			if dependents != None:
				for o in dependents.split(","):
					dependent_parts.append(self.get(o))

			related_parts = []
			if relateds != None:
				for o in relateds.split(","):
					related_parts.append(self.get(o))

			body_part = self.get(i)
			body_part.dependent_parts = dependent_parts
			body_part.related_parts = related_parts

	def get_current_total_health(self):
		number = 0
		for i in self.body_parts:
			number += i.health
		return number

	def update_injury_multiplier(self):
		num =  (self.get_current_total_health() - 500) / (self.max_health - 500)
		self.injury_multiplier = num
		return num

	def update_state(self):
		if self.state == State.DEAD and self.get_current_total_health() > 500:
			self.state = State.ALIVE
			return State.DEAD

		if self.state == State.ALIVE and self.get_current_total_health() < 500:
			self.state = State.DEAD
			return State.DEAD

		return self.state

	def is_alive(self):
		if self.state == State.ALIVE:
			return True
		else:
			return False

	def delete(self):
		for i in self.body_parts:
			del i
		del self

class Body_Part:

	def __init__(self, name, max_health):
		self.name = name
		self.max_health = max_health
		self.health = self.max_health
		self.dependent_parts = []
		self.related_parts = []
		self.state = State.ALIVE

	def change_state(self, new_state):
		self.state = new_state
		return self.state

	def is_alive(self):
		if self.state == State.DEAD:
			return False
		return True

	def is_injured(self):
		if self.health < self.max_health:
			return True
		return False

	def damage_part(self, damage):
		self.health = self.health - damage
		return self.health

	def heal_part(self, amount):
		self.health = self.health + amount
		if self.health > self.max_health:
			self.health = self.max_health
		return self.health

	def resurrect(self):
		if self.state == State.ALIVE:
			return
		self.change_state(State.ALIVE)
		self.health = 1

	def die(self):
		dead_parts = [self]
		self.change_state(State.DEAD)
		self.health = 0
		for i in self.dependent_parts:
			i.health = 0
			i.die()
			dead_parts.append(i)
		return dead_parts

class Combatant(persistent.Persistent):
	def __init__(self, uid, cid):
		self.uid = uid
		self.cid = cid
		self.body = Body(self.uid)
		self.xp = 0

class Player(Combatant):
	def __init__(self, uid, name):
		super().__init__(uid, 0)
		self.name = name
		self.health_update.start()

	@tasks.loop(seconds=120.0)
	async def health_update(self):
		for i in self.body.body_parts:
			if not i.is_alive():
				i.resurrect()
				continue
			elif i.is_injured():
				if random.randrange(0, 3) == 1:
					i.heal_part(random.randrange(i.max_health))

		self.body.update_state()
		self.body.update_injury_multiplier()

	async def get_user(self):
		if self.uid != 0:
			user = await client.fetch_user(self.uid)
			return user
		else:
			return None

	async def get_name(self):
		user = await self.get_user()
		if user != None:
			return user.name
		else:
			return None

	async def get_dm_channel(self):
		user = await self.get_user()
		if user != None:
			channel = user.dm_channel
			if channel == None:
				channel = await user.create_dm()
			return channel
		else:
			return None

	async def dm_user(self, content=None, file=None):
		if (content == None or content == "") and file == None:
			return
		channel = await self.get_dm_channel()
		new_message = await channel.send(content=content, file=file)
		return new_message

class Stan(Combatant):
	def __init__(self, cid):
		super().__init__(0, cid)
		self.cid = cid
		self.weapon_memory_table = {}
		self.damage_table = {}

	def update_weapon_memory(self, weapon):
		if weapon not in self.weapon_memory_table.keys():
			self.weapon_memory_table[weapon] = 1
		else:
			self.weapon_memory_table[weapon] += 1
		return self.weapon_memory_table[weapon] - 1

	def update_damage_table(self, combatant_name, damage):
		if combatant_name not in self.damage_table.keys():
			self.damage_table[combatant_name] = damage
		else:
			self.damage_table[combatant_name] += damage

	def die(self):
		stans.remove(self)
		self.body.delete()
		del self

class Attack:
	def	__init__(self, combatant_attacker, combatant_attacked, initial_weapon=""):
		self.combatant_attacker = combatant_attacker
		self.combatant_attacked = combatant_attacked
		self.body_attacker = self.combatant_attacker.body
		self.body_attacked = self.combatant_attacked.body

		self.weapon = ""
		self.damage = 0

		self.injury_multiplier = self.body_attacker.injury_multiplier
		self.weapon_memory_multiplier = 1

		self.killed_parts = []

		self.stan_attack = False
		if self.combatant_attacker.uid == 0:
			self.stan_attack = True

		attributes = open("text/weapon_attributes.txt", "r").readlines()
		attribute = attributes[random.randrange(len(attributes))]
		self.attribute_name = attribute.split(":")[0].strip()
		self.attribute_multiplier = float(attribute.split(":")[1].strip())

		viable_body_parts = []
		for i in self.body_attacked.body_parts:
			if i.is_alive():
				viable_body_parts.append(i)
		initial_body_part = random.choice(viable_body_parts)

		self.attacked_parts = [initial_body_part]
		viable_body_parts = []
		for i in initial_body_part.related_parts:
			if i.is_alive():
				viable_body_parts.append(i)
		add_more = True
		while add_more:
			if random.randrange(0, 3) == 1:
				add_more = False
			if len(viable_body_parts) < 1:
				break
			part = random.choice(viable_body_parts)
			self.attacked_parts.append(part)
			viable_body_parts.remove(part)

		if self.stan_attack:
			weapon_prefixes = open("text/stan_weapons_prefix.txt", "r").readlines()
			weapon_bases = open("text/stan_weapons_base.txt", "r").readlines()
			weapon_prefix = random.choice(weapon_prefixes).strip()
			weapon_base = random.choice(weapon_bases).strip()
			self.weapon = self.attribute_name + " " + weapon_prefix + weapon_base
			self.damage = round(random.randrange(0, 101) * self.injury_multiplier * self.attribute_multiplier)

			#attack resolution (affecting relating bodies)

			split_damage = math.ceil(self.damage / len(self.attacked_parts))
			for i in self.attacked_parts:
				i.damage_part(split_damage)
				if i.health < 1:
					self.killed_parts.extend(i.die())

			self.body_attacked.update_injury_multiplier()
			self.body_attacked.update_state()

		else:
			if initial_weapon != "":
				self.weapon = self.attribute_name + " " + initial_weapon
				weapon_memory_num = self.combatant_attacked.update_weapon_memory(initial_weapon)
				weapon_memory_multiplier_raw = 1 - (weapon_memory_num * 0.10)
				self.weapon_memory_multiplier = max([0.10, weapon_memory_multiplier_raw])
				
				int_from_weapon_name = int(str(int.from_bytes(initial_weapon.encode(), "little"))[0:2])
				self.damage = round((int_from_weapon_name / 2) * self.injury_multiplier * self.attribute_multiplier * self.weapon_memory_multiplier)

			else:
				self.weapon = ""
				self.damage = round(random.randrange(0, 51) * self.injury_multiplier)

			#attack resolution (affecting relating bodies)

			split_damage = math.ceil(self.damage / len(self.attacked_parts))

			self.combatant_attacked.update_damage_table(self.combatant_attacker.name, split_damage * len(self.attacked_parts))
			split_damage = math.ceil(self.damage / len(self.attacked_parts))
			for i in self.attacked_parts:
				i.damage_part(split_damage)
				if i.health < 1:
					self.killed_parts.extend(i.die())

			self.body_attacked.update_injury_multiplier()
