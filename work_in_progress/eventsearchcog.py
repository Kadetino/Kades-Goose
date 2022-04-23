import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
import pytesseract  # OCR, get string from image
import requests  # Get image from URL
from PIL import Image  # Get image
import io  # Get image
from config import cd_commands, tesseract_cmd_path, prefix


class EventSearchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO Rework database == find better parser

    async def find_event(self, image_output: str, ctx: commands.Context):
        """Search contents of EU4EVENTS table for corresponding event."""
        # Open SQLite connection, extract data and close it
        sql_connection = sl.connect('Goose.db')
        data = sql_connection.execute(
            f"SELECT * FROM EU4EVENTS WHERE trim(event_name) LIKE '{image_output.strip()}'").fetchall()
        sql_connection.close()

        # Process data
        if len(data) == 1:  # One event found.
            # Convert list to tuple
            data = data[0]

            # Get event data
            event_name = str(data[1]).strip()
            event_condition = str(data[2])
            event_mtth = str(data[3])
            event_ie = str(data[4])
            event_choice = str(data[0][5])

            # Making it readable
            event_choice = event_choice.replace("&&&&Option", "\n*Option")
            event_choice = event_choice.replace("\n*Option", "Option", 1)
            stars = ["*****", "****", "***", "**", "*"]
            for star in stars:
                event_condition = event_condition.replace(star, "\n")
                event_mtth = event_mtth.replace(star, "\n")
                event_ie = event_ie.replace(star, "\n")
                event_choice = event_choice.replace(star, "\n")

            # Making Discord embed
            event_embed = discord.Embed(title=event_name, color=discord.Colour.gold())
            event_embed.add_field(name="Trigger", value=event_condition, inline=False)
            event_embed.add_field(name="Mean time to happen", value=event_mtth, inline=False)
            event_embed.add_field(name="Immediate effects", value=event_ie, inline=False)
            event_embed.add_field(name="Options", value=event_choice, inline=False)
            event_embed.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)
        elif len(data) > 1:  # More than 1 event found
            description = ""
            for row in data:
                description += f"`{str(row[1].strip())}` index: {row[0]}\n\n"
            # Making Discord embed
            event_embed = discord.Embed(title="Multiple events found",
                                        description=description,
                                        color=discord.Colour.gold())
        else:  # No events found.
            event_embed = discord.Embed(title="No events found",
                                        description="Sorry, couldn't find anything.",
                                        color=discord.Colour.gold())

        return await ctx.reply(embed=event_embed)
        # return event_embed

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def extract(self, ctx: commands.Context, image_url: str = None):
        """Shows the description of the game event based on the data from the attached screenshot or the URL"""
        # Получить изображение как вложенный файл
        if len(ctx.message.attachments) > 0:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
            image_url = ctx.message.attachments[0]  # This is not string TODO
            image = Image.open(io.BytesIO(await image_url.read()))  # get image from url

            # await ctx.reply(pytesseract.image_to_string(image, config='--psm 6'))
            print(pytesseract.image_to_string(image, lang='eng', config='--psm 6'))
            # search_result = await self.find_event(pytesseract.image_to_string(image, config='--psm 6'), ctx)
        #######################################
        # # Получить изображение по ссылке
        # else:
        #     for url in range(len(img_urls)):
        #         try:
        #             response = requests.get(img_urls[url])
        #
        #         except Exception:
        #             if len(img_urls) > 1:
        #                 current_output = f"{url + 1}) Error: can't recognize the URL"
        #             else:
        #                 current_output = "Error: can't recognize the URL"
        #             await ctx.reply(current_output)
        #
        #         else:
        #             image = Image.open(io.BytesIO(response.content))
        #
        #             # Обработка текста
        #             pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
        #             search_result = self.find_event(pytesseract.image_to_string(image, config='--psm 6'), ctx)
        #             if search_result:
        #                 # Send embed
        #                 await ctx.reply(embed=search_result[1])
        #
        #             else:
        #                 await ctx.reply("Couldn't find the event")

    # @commands.command(pass_context=True)
    # @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    # @commands.guild_only()
    # async def findEvent(self, ctx, *args):
    #     """Searches for event by the specified name"""
    #     # Check whether event name was given
    #     if len(args) == 0:
    #         await ctx.reply(
    #             content=f"No event names provided. Example usage: {prefix}findEvent Court of the Star Chamber")
    #     else:
    #         # Assembling event name from *args
    #         arg_event_name = ""
    #         for i in args:
    #             arg_event_name = arg_event_name + i + " "
    #
    #         # Event search
    #         search_result = self.find_event(arg_event_name, ctx)
    #         if search_result:
    #             # Send embed
    #             await ctx.reply(embed=search_result[1])
    #
    #         else:
    #             await ctx.reply(content=f"Couldn't find the event: \"{arg_event_name}\"")

    # # doesn't work with this db implementation
    #
    # @commands.command(pass_context=True)
    # @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    # @commands.guild_only()
    # async def randomEvent(self, ctx):
    #     """Generates a description for a random event from the database"""
    #     conn = sl.connect('Goose.db')
    #     data = conn.execute("SELECT * FROM EU4EVENTS").fetchall()
    #     conn.close()
    #     names = []
    #     for rows in data:
    #         print(rows)
    #         names.append(rows[1].strip())
    #     for rows in names:
    #         print(rows)
    #     print(len(names))
    #     search_result = db.find_event(names[random.randint(0, len(names) - 1)], ctx)
    #
    #     await ctx.reply(embed=search_result[1])

    @commands.command(pass_context=True)
    async def eventhelp(self, ctx):
        """Shows list and description of all available commands"""
        help_embed = discord.Embed(title='Help', color=0x2faf49)

        help_embed.add_field(name=prefix + 'extract', value='Shows the description of the game event based\
             on the data from the attached screenshot or the URL', inline=False)
        help_embed.add_field(name=prefix + 'findEvent', value='Searches for event by the specified name',
                             inline=False)
        help_embed.add_field(name=prefix + 'randomEvent', value='Shows description of a random event\
             from the database', inline=False)
        help_embed.add_field(name=prefix + 'recentEvents',
                             value='Shows the names of 10 most recent event searches', inline=False)

        help_embed.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=help_embed)


def setup(bot):
    bot.add_cog(EventSearchCog(bot))
