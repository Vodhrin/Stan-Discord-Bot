import discord
from discord.ext import commands

admin_ids = []
temp = open("ids.txt", "r").readlines()
for i in temp:
	admin_ids.append(int(i.strip()))

messages_to_delete = []
combat_messages_query = []
combat_messages_delete = []

prefix = "+"

intents = discord.Intents.all()

client = commands.Bot(command_prefix=prefix, intents=intents)