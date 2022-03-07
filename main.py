import discord
import aiohttp
import warnings
from discord.ext import commands

import config


bot = commands.Bot(command_prefix=config.prefix)
bot.remove_command('help')
warnings.filterwarnings("ignore", category=DeprecationWarning)
bot.session = aiohttp.ClientSession()

@bot.event
async def on_ready():
    print('Logged on as {0.user}!'.format(bot))

bot.load_extension("cogs.eventsearchcog")
bot.load_extension("cogs.fun")
bot.run(config.token)

