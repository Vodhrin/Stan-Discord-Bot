import discord
import random
import time
import asyncio
import hashlib
import os
import numpy
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

	#make all of the attacks actually deal damage to the body part objects and save that in their health_left attribute
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
		vowels = ["a", "e", "i", "o", "u"]
		if i.weapon == "":
			new_message = await channel.send("_" + i.attacker.name + " attacked Stan's " + i.body_part.name + " for " + str(i.damage) + " damage!_")
		else:
			if i.weapon[0] in vowels:
				new_message = await channel.send("_" + i.attacker.name + " attacked Stan's " + i.body_part.name + " with an " + i.weapon + " for " + str(i.damage) + " damage!_")
			else:
				new_message = await channel.send("_" + i.attacker.name + " attacked Stan's " + i.body_part.name + " with a " + i.weapon + " for " + str(i.damage) + " damage!_")
		messages.append(new_message)
		await channel.trigger_typing()
		await asyncio.sleep(0.1)

	await asyncio.sleep(1)

	body_parts_affected = []
	for i in attacks:
		if i.body_part not in body_parts_affected:
			body_parts_affected.append(i.body_part)

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
	image_torso = Image.open("images/body_parts/torso.png").convert("RGBA")
	image_arm_right = Image.open("images/body_parts/arm_right.png").convert("RGBA")
	image_arm_left = Image.open("images/body_parts/arm_left.png").convert("RGBA")
	image_hand_right = Image.open("images/body_parts/hand_right.png").convert("RGBA")
	image_hand_left = Image.open("images/body_parts/hand_left.png").convert("RGBA")
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
		await add_body_image(composite, image_head, (512, 192), False)

	if body.arm_right.is_alive():
		await add_body_image(composite, image_arm_right, (352, 352), True, await get_color(body.arm_right))

	if body.arm_left.is_alive():
		await add_body_image(composite, image_arm_left, (672, 352), True, await get_color(body.arm_left))

	if body.hand_right.is_alive():
		await add_body_image(composite, image_hand_right, (800, 352), True, await get_color(body.hand_right))

	if body.hand_left.is_alive():
		await add_body_image(composite, image_hand_left, (224, 352), True, await get_color(body.hand_left))

	if body.fingers_right.is_alive():
		await add_body_image(composite, image_fingers_right, (832, 352), True, await get_color(body.fingers_right))

	if body.fingers_left.is_alive():
		await add_body_image(composite, image_fingers_left, (192, 352), True, await get_color(body.fingers_left))

	if body.ass_cheek_right.is_alive():
		await add_body_image(composite, image_ass_cheek, (576, 536), True, await get_color(body.ass_cheek_right))

	if body.ass_cheek_left.is_alive():
		await add_body_image(composite, image_ass_cheek, (448, 536), True, await get_color(body.ass_cheek_left))

	if body.leg_right.is_alive():
		await add_body_image(composite, image_leg_right, (616, 624), True, await get_color(body.leg_right))

	if body.leg_left.is_alive():
		await add_body_image(composite, image_leg_left, (408, 624), True, await get_color(body.leg_left))

	if body.foot_right.is_alive():
		await add_body_image(composite, image_hand_right, (656, 736), True, await get_color(body.foot_right))

	if body.foot_left.is_alive():
		await add_body_image(composite, image_hand_left, (368, 736), True, await get_color(body.foot_left))

	if body.toes_right.is_alive():
		await add_body_image(composite, image_toes_right, (672, 768), True, await get_color(body.toes_right))

	if body.toes_left.is_alive():
		await add_body_image(composite, image_toes_left, (352, 768), True, await get_color(body.toes_left))

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

def get_composite_subject(members):

	text = ""

	if len(members) == 1:
		text += members[0].name

	if len(members) == 2:
		for idx, i in enumerate(members):
			text += i.name
			if idx == 0:
				text += " and "

	if len(members) > 2:
		for idx, i in enumerate(members):
			text += i.name
			if idx < (len(members) - 2):
				text += ", "
			if idx == (len(members) - 2):
				text += " and "
	text += " "
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

		self.eye_left = Body_Part("left eye", 25)
		self.eye_right = Body_Part("right eye", 25)
		self.ear_left = Body_Part("left ear", 10)
		self.ear_right = Body_Part("right ear", 10)
		self.nose = Body_Part("nose", 15)
		self.teeth = Body_Part("teeth", 35)
		self.head = Body_Part("head", 100, [self.eye_left, self.eye_right, self.ear_left, self.ear_right, self.nose, self.teeth])
		self.fingers_left = Body_Part("left fingers", 15)
		self.hand_left = Body_Part("left hand", 50, [self.fingers_left])
		self.arm_left = Body_Part("left arm", 100, [self.hand_left])
		self.fingers_right = Body_Part("right fingers", 15)
		self.hand_right = Body_Part("right hand", 50, [self.fingers_right])
		self.arm_right = Body_Part("right arm", 100, [self.hand_right])
		self.toes_left = Body_Part("left toes", 15)
		self.foot_left = Body_Part("left foot", 50, [self.toes_left])
		self.leg_left = Body_Part("left leg", 100, [self.foot_left])
		self.toes_right = Body_Part("right toes", 15)
		self.foot_right = Body_Part("right foot", 50, [self.toes_right])
		self.leg_right = Body_Part("right leg", 100, [self.foot_right])
		self.ass_cheek_left = Body_Part("left ass cheek", 35)
		self.ass_cheek_right = Body_Part("right ass cheek", 35)
		self.pubic_hair = Body_Part("pubic hair", 15)
		self.penis = Body_Part("penis", 15)
		self.testicles = Body_Part("testicles", 15)
		self.torso = Body_Part("torso", 300, [self.head, self.arm_left, self.arm_right, self.leg_left, self.leg_right, self.ass_cheek_left, self.ass_cheek_right, self.pubic_hair, self.penis, self.testicles])

		self.body_parts = [self.eye_left, self.eye_right, self.ear_left, self.ear_right, self.nose, self.teeth, self.head, self.fingers_left, self.hand_left, self.arm_left, self. fingers_right, self.hand_right, self.arm_right, self.toes_left, self.foot_left, self.leg_left, self.toes_right, self.foot_right, self.leg_right, self.ass_cheek_left, self.ass_cheek_right, self.pubic_hair, self.penis, self.testicles, self.torso]

		self.max_health = self.get_current_total_health()

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
	def __init__(self, attacker, damage, body_part, weapon="", adjective=""):
		self.attacker = attacker
		self.damage = damage
		self.body_part = body_part
		self.weapon = weapon
		self.adjective = adjective
		self.health_left = 1
		self.killed_part = False
		self.parts_killed = []

	def resolve_attack(self):
		self.health_left = self.body_part.damage_part(self.damage)
		if self.health_left < 1:
			self.killed_part = True
			self.parts_killed = self.body_part.die()

	def update_parts_killed(self, parts):
		self.parts_killed = parts