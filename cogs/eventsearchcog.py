import discord
import pytesseract
import io
import random
import requests
import database as db
from PIL import Image
from discord.ext import commands
import config

class EventSearchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def extract(self, ctx, *img_urls):
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

                    await ctx.reply(current_output)

                else:
                    img = Image.open(io.BytesIO(await img_url.read()))

                    # Обработка текста
                    pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path

                    search_result = db.find_event(pytesseract.image_to_string(img, config='--psm 6'), ctx)
                    if search_result:
                        event_name = f"Event name: {search_result[0]}"
                        if len(ctx.message.attachments) > 1:
                            event_name = f"{attach + 1}) {event_name}"

                        # Remember event name
                        db.log_event_name(search_result[0])
                        # Send embed
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
                    search_result = db.find_event(pytesseract.image_to_string(img, config='--psm 6'), ctx)
                    if search_result:
                        # Remember event name
                        db.log_event_name(search_result[0])
                        # Send embed
                        await ctx.reply(embed=search_result[1])

                    else:
                        await ctx.reply("Couldn't find the event")

    @commands.command(pass_context=True)
    async def findEvent(self, ctx, *args):
        """Searches for event by the specified name"""
        # Check whether event name was given
        if len(args) == 0:
            await ctx.reply(
                content=f"No event names provided. Example usage: {config.prefix}findEvent Court of the Star Chamber")
        else:
            # Assembling event name from *args
            arg_event_name = ""
            for i in args:
                arg_event_name = arg_event_name + i + " "

            # Event search
            search_result = db.find_event(arg_event_name, ctx)
            if search_result:
                # Remember event name
                db.log_event_name(search_result[0])
                # Send embed
                await ctx.reply(embed=search_result[1])

            else:
                await ctx.reply(content=f"Couldn't find the event: \"{arg_event_name}\"")

    @commands.command(pass_context=True)
    async def randomEvent(self, ctx):
        """Generates a description for a random event from the database"""
        search_result = db.find_event(db.df['Name of the event'][random.randint(0, len(db.df.index) - 1)], ctx)

        await ctx.reply(embed=search_result[1])

    @commands.command(pass_context=True)
    async def recentEvents(self, ctx):
        """Shows the history of recent event requests"""
        # Проверка на существование файла searchEventLog.txt
        try:
            with open("logs/searchEventLog.txt", "r"):
                pass
        except FileNotFoundError:  # Создание файла, если его нет
            with open("logs/searchEventLog.txt", "w"):
                pass

        # Получение названий из файла
        with open("logs/searchEventLog.txt", "r") as searchLog:
            lines = searchLog.readlines()

        # Проверка на наличие элементов
        if len(lines) < 1:
            await ctx.reply("No events available")  # Неудача
        else:
            description = ""  # то что пойдет на выход в эмбед
            counter = 1  # для формирования нумерации в эмбеде

            # Формирование описания эмбеда
            for line in reversed(lines):
                temp = f"{counter}. {line}\n"  # Например: 1. The fifth of november\n
                description += temp
                counter += 1
                if counter == 11:
                    break

            # Отправка сообщения
            embedVar = discord.Embed(title="10 Most recent searched events", description=description, color=0x12ffe3)
            embedVar.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)

            await ctx.reply(embed=embedVar)

def setup(bot):
    bot.add_cog(EventSearchCog(bot))