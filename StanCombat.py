import discord
import random
import time
import asyncio
import hashlib
import os
import numpy
import math
from operator import sub
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from PIL.ImageColor import getrgb

from StanLanguage import *

async def combat_query(message_group, messages, bodies, flags, channel):

	#add the initiating user's command message to list of messages to delete
	messages.extend(message_group)

	#determining if we need to start a new fight or if one is already occuring
	already_fighting = False
	for i in bodies:
		if i.channel is channel:
			already_fighting = True

	for i in message_group:
		if i.content.split()[2] == "start":
			if already_fighting:
				flags[channel] = True
				new_message = await channel.send("We're already fighting, retarded faggot.")
				messages.extend(message_group)
				flags[channel] = False
				return
			else:
				flags[channel] = True
				await combat_clear_messages(channel, message_group, messages)
				await combat_start(channel, messages, bodies)
				flags[channel] = False

	#attacking
	body = None

	messages_attackers = []
	for i in message_group:
		if i.content.split()[2] == "attack":
			messages_attackers.append(i)


	if len(messages_attackers) > 0:
		in_fight = False
		for i in bodies:
			if i.channel is channel:
				body = i
				in_fight = True

		#tell user to start a fight first
		if not in_fight:
			flags[channel] = True
			await channel.trigger_typing()
			await combat_clear_messages(channel, message_group, messages)
			new_message = await channel.send("Start a fight first, retard.")
			messages.append(new_message)
			flags[channel] = False
			return

		#attack
		else:

			flags[channel] = True
			await channel.trigger_typing()

			#delete all previous fighting messages in this channel
			await combat_clear_messages(channel, message_group, messages)

			#run all the actual code to do with fight calculations, combat image, etc
			await combat_update(messages_attackers, channel, messages, body)
			flags[channel] = False
			return

async def combat_start(channel, messages, bodies):

	#instantiates a new combat body class and adds it to the list of current combat bodies
	body = Combat_Body(channel)
	bodies.append(body)
	new_message = await channel.send("Lets go, nigger.")
	messages.append(new_message)
	return

async def combat_update(messages_attackers, channel, messages, body):

	overall_message = ""
	attackers = []
	for i in messages_attackers:
		attackers.append(i.author)

	#make a list of only currently living bodyparts
	viable_body_parts = []
	for i in body.body_parts:
		if i.state != Body_Part.states["Dead"]:
			viable_body_parts.append(i)

	#generate a list of attacks, one for each attacker
	attacks = []
	if len(viable_body_parts) > len(attackers):
		for i in messages_attackers:
			mult = 1
			weapon = ""

			text = i.content.split()
			del text[0:3]
			text = " ".join(text)

			if len(i.content.split()) > 3:
				weapon, mult = get_weapon_info(text)

			index = random.randrange(len(viable_body_parts))
			damage = round(random.randrange(0, 50) * mult)
			if weapon != "":	
				num = int(str(int.from_bytes(text.encode(), "little"))[0:2])
				damage = round((num / 2) * mult)
				
			body_part = viable_body_parts[index]
			del viable_body_parts[index]

			attack = Attack(i.author, damage, body_part, weapon)
			attacks.append(attack)
	else:
		for i in messages_attackers:
			mult = 1
			weapon = ""

			text = i.content.split()
			del text[0:3]
			text = " ".join(text)

			if len(i.content.split()) > 3:
				weapon, mult = get_weapon_info(text)

			index = random.randrange(len(viable_body_parts))
			damage = round(random.randrange(0, 50) * mult)
			bopy_part = viable_body_parts[index]

			attack = Attack(i.author, damage, body_part, weapon)
			attacks.append(attack)

	#determine if each attack hits other parts around it (total damage stays the same, just split among the parts)
	for i in attacks:
		find_more_parts = True
		new_parts = i.body_part.related_parts

		for i in new_parts:
			if i.state == Body_Part.states["Dead"]:
				new_parts.remove(i)

		while new_parts:
			idx = 0
			if len(new_parts) != 1:
				idx = random.randrange(len(new_parts))

			if random.randrange(0, 3) == 1:
				i.additional_body_parts.append(new_parts[idx])
			del new_parts[idx]

	#make all of the attacks actually deal damage to the body part(s) objects and save that in their health_left attribute
	for i in attacks:
		i.resolve_attack()

	#print combat image
	filename = "cache/" + hashlib.md5(messages_attackers[0].jump_url.encode()).hexdigest() + ".png"
	image = await create_combat_image(body)
	image.save(filename)
	new_message = await channel.send(file=discord.File(filename, "rapedbystan.png"))
	messages.append(new_message)
	os.remove(filename)

	for i in attacks:
		#initial attack acknowledgement
		new_message = ""
		maybe_total = ""
		parts = [i.body_part]
		parts.extend(i.additional_body_parts)
		names = []
		for o in parts:
			names.append(o.name)
		if len(parts) > 1:
			maybe_total = " total"
		vowels = ["a", "e", "i", "o", "u"]
		if i.weapon == "":
			new_message = await channel.send("_" + i.attacker.name + " attacked Stan's " + get_composite_noun(names) + " for " + str(i.damage) + maybe_total + " damage!_")
		else:
			if i.weapon[0] in vowels:
				new_message = await channel.send("_" + i.attacker.name + " attacked Stan's " + get_composite_noun(names) + " with an " + i.weapon + " for " + str(i.damage) + maybe_total + " damage!_")
			else:
				new_message = await channel.send("_" + i.attacker.name + " attacked Stan's " + get_composite_noun(names) + " with a " + i.weapon + " for " + str(i.damage) + maybe_total + " damage!_")
		messages.append(new_message)
		await channel.trigger_typing()
		await asyncio.sleep(0.1)

	await asyncio.sleep(1)

	body_parts_affected = []
	for i in attacks:
		if i.body_part not in body_parts_affected:
			body_parts_affected.append(i.body_part)
		for o in i.additional_body_parts:
			if o not in body_parts_affected:
				body_parts_affected.append(o)

	for i in body_parts_affected:
		if i.state != Body_Part.states["Dead"]:
			new_message = await channel.send("_Stan's " + i.name + " now has " + str(i.health) + " health left!_")
			messages.append(new_message)
			if random.randrange(0, 3) == 1:
				await channel.trigger_typing()
				await asyncio.sleep(0.05)

				#random chance to say bodypart has affliction
				if random.randrange(0, 2) == 1:
					text = "**_Stan's " + i.name + " is now <aa>!_**"
				else:
					text = "**_Stan's " + i.name + " is now <aa> <ad>!_**"
				new_message = await channel.send(replace_text_tags(text))
				messages.append(new_message)

	total_parts_killed = []
	temp = []
	for i in attacks:
		temp.extend(i.parts_killed)
	for i in temp:
		if i not in total_parts_killed:
			total_parts_killed.append(i)

	text = "_Stan's "

	#if only one bodypart died
	if len(total_parts_killed) == 1:
		new_message = await channel.send("_Stan's " + total_parts_killed[0].name + " is now " + Body_Part.states["Dead"] + "!_")
		messages.append(new_message)
	#if multiple died
	elif len(total_parts_killed) == 2:
		for idx, i in enumerate(total_parts_killed):
			text += i.name
			if idx == 0:
				text += " and "
		text += " are now " + Body_Part.states["Dead"] + "!_"
		new_message = await channel.send(text)
		messages.append(new_message)
	elif len(total_parts_killed) > 2:
		for idx, i in enumerate(total_parts_killed):
			text += i.name
			if idx < (len(total_parts_killed) - 2):
				text += ", "
			if idx == (len(total_parts_killed) - 2):
				text += " and "
		text += " are now " + Body_Part.states["Dead"] + "!_"
		new_message = await channel.send(text)
		messages.append(new_message)

	#random chance to say gay shit when bodypart dies
	if len(total_parts_killed) > 0:
		idx = random.randrange(len(total_parts_killed))
		if random.randrange(0, 3) == 1:
			significant_part = total_parts_killed[idx]
			new_message = await channel.send("_Stan cries out!_")
			messages.append(new_message)
			await asyncio.sleep(0.5)
			new_message = await channel.send(replace_text_tags("**Oh god, my " + significant_part.name + "! It looks like a <vpa> <a> <ns> now!**"))
			messages.append(new_message)

	#if stan's health is now below 500 he overall dies
	if body.get_current_total_health() < 500:
		body.remove(body)
		body.die()
		new_message = await channel.send(replace_text_tags("_Stan has been vanquished! His <vpa> body now resembles a pile of <a> <np>!_"))
		messages.append(new_message)
		await channel.trigger_typing()
		await asyncio.sleep(1.5)
		new_message = await channel.send(replace_text_tags("**I will return, you <a> <ns> <adds>.**"))
		messages.append(new_message)
		asyncio.sleep(10)
		await combat_clear_messages(channel, messages_attackers, messages)
		return

async def combat_clear_messages(channel, message_group, messages):

	messages_to_delete = []
	for i in messages:
		if i.channel == channel:
			messages_to_delete.append(i)
	while messages_to_delete:
		for i in messages_to_delete:
			try:
				await i.delete()
				messages_to_delete.remove(i)
			except (discord.Forbidden, discord.NotFound):
				messages_to_delete.remove(i)
			except discord.HTTPException:
				pass
	messages.extend(message_group)

async def create_combat_image(body):

	image_background = Image.open("images/background.png").convert("RGBA")
	image_head = Image.open("images/stanface.png").convert("RGBA")
	image_ear = Image.open("images/body_parts/ear.png").convert("RGBA")
	image_torso = Image.open("images/body_parts/torso.png").convert("RGBA")
	image_arm = Image.open("images/body_parts/arm.png").convert("RGBA")
	image_hand = Image.open("images/body_parts/hand.png").convert("RGBA")
	image_fingers_right = Image.open("images/body_parts/fingers_right.png").convert("RGBA")
	image_fingers_left = Image.open("images/body_parts/fingers_left.png").convert("RGBA")
	image_leg_right = Image.open("images/body_parts/leg_right.png").convert("RGBA")
	image_leg_left = Image.open("images/body_parts/leg_left.png").convert("RGBA")
	image_toes_right = Image.open("images/body_parts/toes_right.png").convert("RGBA")
	image_toes_left = Image.open("images/body_parts/toes_left.png").convert("RGBA")
	image_ass_cheek = Image.open("images/body_parts/ass_cheek.png").convert("RGBA")
	image_penis = Image.open("images/body_parts/penis.png").convert("RGBA")
	image_testicles = Image.open("images/body_parts/testicles.png").convert("RGBA")

	mult = (body.get_current_total_health() - 500) / (body.max_health - 500)
	file_name = "images/healthbar/" + str(56 - round(mult * 55)) + ".png"  

	image_healthbar = Image.open(file_name).convert("RGBA")

	composite = image_background

	if body.head.is_alive():
		await add_head_stan_image(composite, (512, 192), body)

	if body.ear_r.is_alive():
		await add_body_image(composite, image_ear, (640, 192), True, await get_color(body.ear_r))

	if body.ear_l.is_alive():
		await add_body_image(composite, image_ear, (384, 192), True, await get_color(body.ear_l))

	if body.arm_r.is_alive():
		await add_body_image(composite, image_arm, (672, 352), True, await get_color(body.arm_r))

	if body.arm_l.is_alive():
		await add_body_image(composite, image_arm, (352, 352), True, await get_color(body.arm_l))

	if body.hand_r.is_alive():
		await add_body_image(composite, image_hand, (800, 352), True, await get_color(body.hand_r))

	if body.hand_l.is_alive():
		await add_body_image(composite, image_hand, (224, 352), True, await get_color(body.hand_l))

	if body.fingers_r.is_alive():
		await add_body_image(composite, image_fingers_right, (832, 352), True, await get_color(body.fingers_r))

	if body.fingers_l.is_alive():
		await add_body_image(composite, image_fingers_left, (192, 352), True, await get_color(body.fingers_l))

	if body.ass_cheek_r.is_alive():
		await add_body_image(composite, image_ass_cheek, (576, 536), True, await get_color(body.ass_cheek_r))

	if body.ass_cheek_l.is_alive():
		await add_body_image(composite, image_ass_cheek, (448, 536), True, await get_color(body.ass_cheek_l))

	if body.leg_r.is_alive():
		await add_body_image(composite, image_leg_right, (616, 624), True, await get_color(body.leg_r))

	if body.leg_l.is_alive():
		await add_body_image(composite, image_leg_left, (408, 624), True, await get_color(body.leg_l))

	if body.foot_r.is_alive():
		await add_body_image(composite, image_hand, (656, 736), True, await get_color(body.foot_r))

	if body.foot_l.is_alive():
		await add_body_image(composite, image_hand, (368, 736), True, await get_color(body.foot_l))

	if body.toes_r.is_alive():
		await add_body_image(composite, image_toes_right, (672, 768), True, await get_color(body.toes_r))

	if body.toes_l.is_alive():
		await add_body_image(composite, image_toes_left, (352, 768), True, await get_color(body.toes_l))

	if body.penis.is_alive():
		await add_body_image(composite, image_penis, (512, 640), True, await get_color(body.penis))

	if body.testicles.is_alive():
		await add_body_image(composite, image_testicles, (512, 608), True, await get_color(body.testicles))

	if body.torso.is_alive():
		await add_body_image(composite, image_torso, (512, 448), True, await get_color(body.torso))

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

async def weight_colors(color_1, color_2, weight_towards_color_1):

	w_1 = weight_towards_color_1
	w_2 = 1 - weight_towards_color_1

	x_1, x_2, x_3 = color_1
	z_1, z_2, z_3 = color_2

	return (round(x_1*w_1 + z_1*w_2), round(x_2*w_1 + z_2*w_2), round(x_3*w_1 + z_3*w_2))

async def get_color(body_part):

	color = await weight_colors(getrgb("red"), getrgb("white"), 1 - body_part.health / body_part.max_health)
	return color

async def add_head_stan_image(image_background, position, body):

	head = body.head
	image = Image.open("images/stanface.png").convert("RGBA")
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

def get_composite_noun(words):

	text = ""

	if len(words) == 1:
		text += words[0]

	if len(words) == 2:
		for idx, i in enumerate(words):
			text += i
			if idx == 0:
				text += " and "

	if len(words) > 2:
		for idx, i in enumerate(words):
			text += i
			if idx < (len(words) - 2):
				text += ", "
			if idx == (len(words) - 2):
				text += " and "
	return text

def get_weapon_info(name):
	infos = open("text/weapon_attributes.txt", "r").readlines()

	info = infos[random.randrange(len(infos))]

	full_name = info.split(":")[0] + " " + name
	mult = float(info.split(":")[1].strip())

	return (full_name, mult)

class Combat_Body:
	def __init__(self, channel):
		self.channel = channel

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
		self.pubic_hair = None
		self.penis = None
		self.testicles = None
		self.torso = None

		self.body_parts = []

		self.init_body_parts()

		self.max_health = self.get_current_total_health()

	def get(self, attrname):
		return getattr(self, attrname)

	def set(self, attrname, value):
		return setattr(self, attrname, value)

	def init_body_parts(self):

		infos = open("text/body_part_infos.txt", "r").readlines()
		dependencies = open("text/body_part_dependencies.txt", "r").readlines()
		relations = open("text/body_part_relations.txt", "r").readlines()

		#instantiate all of the parts with only names and health first
		for i in list(vars(self).keys())[1:28]:

			info = None

			for o in infos:
				if o.startswith(i):
					info = o.strip().split(":")[1]

			name = info.split(",")[0]
			health = int(info.split(",")[1])

			self.set(i, Body_Part(name, health))
			self.body_parts.append(self.get(i))

		for i in list(vars(self).keys())[1:28]:

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

	def die(self):
		for i in self.body_parts:
			del i
		del self

class Body_Part:

	states = {"Alive":"healthy and functional", "Dead":"destroyed", "Damaged":"damaged"}

	def __init__(self, name, max_health):
		self.name = name
		self.max_health = max_health
		self.health = self.max_health
		self.dependent_parts = []
		self.related_parts = []
		self.state = Body_Part.states["Alive"]

	def change_state(self, new_state):
		self.state = new_state
		return self.state

	def is_alive(self):
		if self.state == Body_Part.states["Dead"]:
			return False
		return True

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

class Attack:
	def __init__(self, attacker, damage, body_part, weapon=""):
		self.attacker = attacker
		self.damage = damage
		self.body_part = body_part
		self.additional_body_parts = []
		self.weapon = weapon
		self.parts_killed = []

	def resolve_attack(self):

		num = 1 + len(self.additional_body_parts)

		split_damage = math.floor(self.damage / num)

		body_parts_to_resolve = [self.body_part]
		body_parts_to_resolve.extend(self.additional_body_parts)

		for i in body_parts_to_resolve:
			i.damage_part(split_damage)
			if i.health < 1:
				self.parts_killed.extend(i.die())

	def update_parts_killed(self, parts):
		self.parts_killed = parts