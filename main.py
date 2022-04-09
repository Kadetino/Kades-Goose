import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import os  # add all Discord.py cogs from directory
import aiohttp  # For direct API requests and webhooks
import warnings  # For direct API requests and webhooks

import config  # Global settings

# TODO update code to the latest discord.py version
# TODO Documentation / proper help command
# Creating Bot
intents = discord.Intents.default()  # all default enabled intents
intents.members = True  # Enabling priviliged intent "Members"
owners = [231388394360537088]  # Kadetino
bot = commands.Bot(command_prefix=commands.when_mentioned_or(config.prefix), owner_ids=set(owners), intents=intents)
bot.remove_command('help')  # help command probably needs to be reworked

# For Duels and webhooks
warnings.filterwarnings("ignore", category=DeprecationWarning)
bot.session = aiohttp.ClientSession()


@bot.event
async def on_ready():
    print('Logged on as {0.user}!'.format(bot))
    await bot.change_presence(activity=discord.Game(name="Honk! Honk!"))


# Load all cogs
for cog_name in os.listdir("./cogs"):
    if cog_name.endswith(".py"):
        bot.load_extension(f"cogs.{cog_name[:-3:]}")

# Run
bot.run(config.token)
