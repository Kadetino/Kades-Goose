import discord
from discord.ext import commands
# try:
#     from PIL import Image
# except ImportError:
#     import Image
# import pytesseract

import config

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('Logged on as {0.user}!'.format(bot))


@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)


@bot.command(pass_context=True)
async def addrole(ctx, message):
    user = ctx.author
    role = discord.utils.get(user.guild.roles, name="huh")
    await user.add_roles(role)


@bot.event
async def on_message(message):
    if message.content.startswith('$hello'):
        await message.channel.send("pies are better than cakes. change my mind.")

    await bot.process_commands(message)

bot.run(config.token)
