import discord
import pytesseract
import io
import requests
import random
from discord.ext import commands
from PIL import Image


import config
import database as db

prefix = "--"
bot = commands.Bot(command_prefix=prefix)
bot.remove_command('help')


@bot.event
async def on_ready():
    print('Logged on as {0.user}!'.format(bot))


@bot.command(pass_context=True)
async def extract(ctx, *img_urls):
    """Shows the description of the game event based on the data from the attached screenshot or the URL"""
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

                search_result = db.find_event(pytesseract.image_to_string(img, config='--psm 6'),ctx)
                if search_result:
                    event_name = f"Event name: {search_result[0]}"
                    if len(ctx.message.attachments) > 1:
                        event_name = f"{attach + 1}) {event_name}"

                    # Запись в файл, запоминающий названия последних найденных событий
                    with open("searchEventLog.txt", "a") as eventLog:
                        eventLog.write(event_name[12:] + "\n")

                    await ctx.reply(embed=search_result[1])

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
                await ctx.reply(current_output)

            else:
                img = Image.open(io.BytesIO(response.content))

                # Обработка текста
                pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path
                search_result = db.find_event(pytesseract.image_to_string(img, config='--psm 6'),ctx)
                if search_result:
                    event_name = f"Event name: {search_result[0]}"
                    if len(img_urls) > 1:
                        event_name = f"{url + 1}) {event_name}"

                    # Запись в файл, запоминающий названия последних найденных событий
                    with open("searchEventLog.txt", "a") as eventLog:
                        eventLog.write(event_name[12:] + "\n")

                    await ctx.reply(embed=search_result[1])

                else:
                    await ctx.reply("Couldn't find the event")


@bot.command(pass_context=True)
async def findEvent(ctx, *args):
    """Searches for event by the specified name"""
    # Check whether event name was given
    if len(args) == 0:
        await ctx.reply(content=f"No event names provided. Example usage: {prefix}findEvent Court of the Star Chamber")
    else:
        # Assembling event name from *args
        arg_event_name = ""
        for i in args:
            arg_event_name = arg_event_name + i + " "

        # Event search
        search_result = db.find_event(arg_event_name,ctx)
        if search_result:
            event_name = f"Event name: {search_result[0]}"

            # to do
            with open("searchEventLog.txt", "a") as eventLog:
                eventLog.write(event_name[12:] + "\n")

            await ctx.reply(embed=search_result[1])

        else:
            await ctx.reply(content=f"Couldn't find the event: \"{arg_event_name}\"")


@bot.command(pass_context=True)
async def randomEvent(ctx):
    """Generates a description for a random event from the database"""
    search_result = db.find_event(db.df['Name of the event'][random.randint(0, len(db.df.index)-1)],ctx)

    await ctx.reply(embed=search_result[1])


@bot.command(pass_context=True)
async def recentEvents(ctx):
    """Shows the history of recent event requests"""
    # Проверка на существование файла searchEventLog.txt
    try:
        with open("searchEventLog.txt", "r"):
            pass
    except FileNotFoundError: # Создание файла, если его нет
        with open("searchEventLog.txt", "w"):
            pass

    # Получение названий из файла
    with open("searchEventLog.txt", "r") as searchLog:
        lines = searchLog.readlines()

    # Проверка на наличие элементов
    if len(lines) < 1:
        await ctx.reply("No events available") # Неудача
    else:
        description = "" # то что пойдет на выход в эмбед
        counter = 1 # для формирования нумерации в эмбеде

        # Формирование описания эмбеда
        for line in reversed(lines):
            temp = f"{counter}. {line}\n" # Например: 1. The fifth of november\n
            description += temp
            counter += 1
            if counter==11:
                break

        # Отправка сообщения
        embedVar = discord.Embed(title="10 Most recent searched events",description=description, color=0x12ffe3)
        embedVar.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=embedVar)


@bot.command(pass_context=True)
async def help(ctx):
    """Shows list and description of all available commands"""
    embedVar = discord.Embed(title='Help', color=0x2faf49)

    embedVar.add_field(name=prefix+'extract', value='Shows the description of the game event based\
         on the data from the attached screenshot or the URL', inline=False)
    embedVar.add_field(name=prefix+'findEvent', value='Searches for event by the specified name', inline=False)
    embedVar.add_field(name=prefix+'randomEvent', value='Shows description of a random event\
         from the database', inline=False)
    embedVar.add_field(name=prefix+'recentEvents', value='Shows the names of 10 most recent event searches', inline=False)

    embedVar.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)
    
    await ctx.reply(embed=embedVar)


@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    """Выключить бота, используя Discord-чат"""
    await ctx.bot.logout()


bot.run(config.token)
