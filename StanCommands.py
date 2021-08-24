import discord
import random
import time
import asyncio
import shelve
from discord.ext import commands

from Config import *
from StanCombat import *
from StanLanguage import *
from StanTunes import *

async def is_admin(ctx):

	return ctx.author.id in admin_ids

@client.command()
@commands.check(is_admin)
async def disconnect(ctx):
	for i in client.voice_clients:
		if i.guild is ctx.author.guild:
			await i.disconnect()
			i.cleanup()
			print("Disconnected from voice channel " + i.channel.name)

@client.command()
@commands.check(is_admin)
async def mass_disconnect(ctx):
	for i in client.voice_clients:
		await i.disconnect()
		i.cleanup()
		print("Disconnected from voice channel " + i.channel.name)

@client.command()
@commands.check(is_admin)
async def purge(ctx):
	if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
		await ctx.channel.purge(limit=10, check=is_me)
		print(ctx.channel.name + " in the guild " + ctx.guild.name + " has been purged")

@client.command()
@commands.check(is_admin)
async def mass_purge(ctx):
	for guild in client.guilds:
		for channel in guild.text_channels:
			if channel.permissions_for(guild.me).manage_messages:
				await channel.purge(limit=10, check=is_me)
				print(channel.name + " in the guild " + guild.name + " has been purged")

@client.command()
async def combat(ctx):
	if isinstance(ctx.channel, discord.DMChannel):
		await ctx.send("I can't do that here, retard.")
		return

	if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:

		if ctx.channel.permissions_for(ctx.guild.me).send_messages:
			return

		await ctx.send("I can't do that here, retard.")
		return

	await ctx.channel.trigger_typing()
	await query(QueryType.ATTACK, ctx.channel, ctx.message)

@client.command(name="combat-status")
async def combat_status(ctx):
	if isinstance(ctx.channel, discord.DMChannel):
		await ctx.send("I can't do that here, retard.")
		return

	if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:

		if ctx.channel.permissions_for(ctx.guild.me).send_messages:
			return

		await ctx.send("I can't do that here, retard.")
		return

	await query(QueryType.STATUS, ctx.channel, ctx.message)

@client.command(name="combat-ability")
async def combat_ability(ctx):
	if isinstance(ctx.channel, discord.DMChannel):
		await ctx.send("I can't do that here, retard.")
		return

	if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:

		if ctx.channel.permissions_for(ctx.guild.me).send_messages:
			return

		await ctx.send("I can't do that here, retard.")
		return

	await query(QueryType.ABILITY, ctx.channel, ctx.message)

@client.command(name="combat-reset-stan")
@commands.check(is_admin)
async def combat_reset_stan(ctx):

	await query(QueryType.RESET_STAN, ctx.channel, ctx.message)

@client.command()
async def play(ctx, arg):
	if arg == None:
		return

	await tunes_query(ctx.message)

@client.command()
async def sussify(ctx, *, arg):
	text = advanced_auto_text_replace(arg)
	try:
		await ctx.send(text)
	except:
		await ctx.send(replace_text_tags("I <ad> shit myself"))

@client.command()
async def niggerfy(ctx, *, arg):
	new_content = replace_text_by_pos_tag(arg, "nigger", "NN", "NNP")
	new_content = replace_text_by_pos_tag(new_content, "niggers", "NNS", "NNPS")
	try:
		await ctx.send(new_content)
	except:
		await ctx.send(replace_text_tags("I <ad> shit myself"))

@client.command()
async def suggest(ctx, *, arg):
	path = "cache/suggestions.txt"
	if os.path.isfile(path):
		file = open(path, "r")
		text = file.read()
		file.close()
	else:
		text = ""
	text += ctx.author.name
	text += " - " + arg + "\n\n"
	file = open(path, "w")
	file.write(text)
	file.close()

	text = "Thank you for your <a> suggestion."
	await ctx.send(replace_text_tags(text))

@client.command()
@commands.check(is_admin)
async def get_weapon_damage(ctx, *, arg):
	num = int(str(int.from_bytes(arg.encode(), "little"))[0:2])

	await ctx.send(str(num/2))

@client.command()
async def dbtest(ctx):
	if ctx.author.id not in admin_ids:
		return

def is_me(m):
	
    return m.author == client.user