import discord
import pytesseract
import io
import requests
from discord.ext import commands
from PIL import Image

import config
import database as db

bot = commands.Bot(command_prefix='--')


@bot.event
async def on_ready():
    print('Logged on as {0.user}!'.format(bot))


@bot.command(pass_context=True)
async def extract(ctx, *img_urls):
    # Получить изображение как вложенный файл
    if ctx.message.attachments:
        for attach in range(len(ctx.message.attachments)):
            try:
                img_url = ctx.message.attachments[attach]
            except Exception:
                current_output = 'Error: can\'t recognize attached file'
                if len(ctx.message.attachments) > 1:
                    current_output = f'{attach + 1}) Error: can\'t recognize attached file'

                await ctx.send(current_output)

            else:
                img = Image.open(io.BytesIO(await img_url.read()))

                # Обработка текста
                pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path

                search_result = db.find_event(pytesseract.image_to_string(img))
                if search_result:
                    event_name = f"Event name: {search_result[0]}"
                    if len(ctx.message.attachments) > 1:
                        event_name = f"{attach + 1}) {event_name}"
                    temp = search_result[1].replace("Option", "\n*Option")
                    temp = temp.replace("Base mean time to happen", "\n*Base mean time to happen")
                    temp = temp.replace("*****", "\n     ")
                    temp = temp.replace("****", "\n   ")
                    temp = temp.replace("***", "\n  ")
                    temp = temp.replace("**", "\n ")
                    temp = temp.replace("*", "\n")
                    embedVar = discord.Embed(title=event_name, color=0x19ffe3)
                    embedVar.add_field(name="Description", value=temp, inline=False)
                    embedVar.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)
                    await ctx.reply(embed=embedVar)

                else:
                    await ctx.message.channel.send("Couldn't find the event")

    # Получить изображение по ссылке
    else:
        for url in range(len(img_urls)):
            try:
                response = requests.get(img_urls[url])

            except Exception:
                if len(img_urls) > 1:
                    current_output = f"{url + 1}) Error: can't recognize the URL"
                else:
                    current_output = "Error: can't recognize the URL"
                await ctx.send(current_output)

            else:
                img = Image.open(io.BytesIO(response.content))

                # Обработка текста
                pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path
                search_result = db.find_event(pytesseract.image_to_string(img))
                if search_result:
                    event_name = f"Event name: {search_result[0]}"
                    if len(img_urls) > 1:
                        event_name = f"{url + 1}) {event_name}"

                    temp = search_result[1].replace("Option", "\n*Option")
                    temp = temp.replace("Base mean time to happen", "\n*Base mean time to happen")
                    temp = temp.replace("*****", "\n     ")
                    temp = temp.replace("****", "\n   ")
                    temp = temp.replace("***", "\n  ")
                    temp = temp.replace("**", "\n ")
                    temp = temp.replace("*", "\n")
                    embedVar = discord.Embed(title=event_name, color=0x19ffe3)
                    embedVar.add_field(name="Description", value=temp, inline=False)
                    embedVar.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)
                    await ctx.reply(embed=embedVar)

                else:
                    await ctx.message.channel.send("Couldn't find the event")


@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    """Выключить бота, используя Discord-чат"""
    await ctx.bot.logout()


bot.run(config.token)
