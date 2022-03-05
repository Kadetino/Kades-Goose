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


@bot.command(pass_context=True)
async def help(ctx):
    """Shows list and description of all available commands"""
    embedVar = discord.Embed(title='Help', color=0x2faf49)

    embedVar.add_field(name=config.prefix+'extract', value='Shows the description of the game event based\
         on the data from the attached screenshot or the URL', inline=False)
    embedVar.add_field(name=config.prefix+'findEvent', value='Searches for event by the specified name', inline=False)
    embedVar.add_field(name=config.prefix+'randomEvent', value='Shows description of a random event\
         from the database', inline=False)
    embedVar.add_field(name=config.prefix+'recentEvents', value='Shows the names of 10 most recent event searches', inline=False)

    embedVar.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)
    
    await ctx.reply(embed=embedVar)

bot.load_extension("cogs.eventsearchcog")
bot.load_extension("cogs.fun")
bot.run(config.token)

