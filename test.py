import discord
from discord.ext import commands

TOKEN = open("token.txt","r").readline()

intents = discord.Intents.all()

client = commands.Bot(command_prefix='+', intents=intents)

@client.command()
async def poop(ctx):
    await ctx.send("arg")
    print("arg")

client.run(TOKEN)