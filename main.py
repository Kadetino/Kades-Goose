import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import os  # add all Discord.py cogs from directory
import aiohttp  # For direct API requests - duel cog
import warnings  # For direct API requests - duel cog

import config  # Global settings

# Creating Bot
bot = commands.Bot(command_prefix=config.prefix)
bot.remove_command('help')  # help command probably needs to be reworked

# For Duels
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
