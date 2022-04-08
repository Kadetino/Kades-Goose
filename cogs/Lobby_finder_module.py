import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
from dateutil import parser, tz  # Epoch time converter

import config  # Global settings


class Lobby:  # needs to be in non-cog file or smth
    #######
    # Start: Lobby_start
    #######
    # Lobby_start format: 2014-09-26 12:24:23
    # inputing lobby start from discord: --myCommand "2014-09-26 12:24:23"
    # https://stackoverflow.com/questions/26016025/convert-string-to-datetime-to-epoch
    # convert lobby_start to epoch and then use epoch like <t:1649357488:R>
    # https://www.reddit.com/r/discordapp/comments/ob2h2l/discord_added_new_timestamp_formatting/
    #
    # None if not provided

    #######                                         |#######
    # Name                                          |# author
    #######                                         |#######
    # name of the league, multiplayer gathering etc |# actually, author.id is enough
    #                                               |# id is like 950687118986981416
    # maybe random name if none provided            |# Mandatory

    #######                         |#######                                                    |#######
    # Guild                         |# Discord invite link                                      |# Guild
    #######                         |#######                                                    |#######
    # Guild id                      |# probably check using regex if it's discord invite link   |# Guild id
    # smth like 621269169572151296  |#                                                          |# smth like 621269169572151296
    #                               |#                                                          |#
    # Mandatory                     |# Mandatory                                                |# Mandatory

    #######
    # Description
    #######
    # promotional message place?
    #
    # optional

    def __init__(self, lobby_name: str, author: int, lobby_start: str, invite_link: str, guild: int, desc: str):
        self.lobby_name = lobby_name
        self.author = author
        self.lobby_start = lobby_start
        self.invite_link = invite_link
        self.guild = guild
        self.desc = desc

    def yep(self):
        """This is for debug. Remove later."""
        print(f"Lobby name: {self.lobby_name}")
        print(f"Hosting user name: {self.author}")
        print(f"Lobby starts: {self.lobby_start}")
        print(f"Discord invite to host's server: {self.invite_link}")
        print(f"Hosting guild id: {self.guild}")
        print(f"Description: {self.desc}")


class LobbyFinderModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="Команда", pass_context=True)
    @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def temp(self, ctx: commands.Context):
        oops = Lobby("Howdy", ctx.author.id, "2014-09-26 12:24:23", "not a link", ctx.guild.id, "Good bye")
        oops.yep()
        return await ctx.reply("peepeepoopoo")

    @commands.command(pass_context=True)
    @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def epoch_test(self, ctx: commands.Context, date: str):
        """Converts string to epoch - maybe store start as epoch (int) and not str?"""
        timezone = {"CET": tz.gettz('EU/Central')}  # not sure if it works
        epoch = parser.parse(date, tzinfos=timezone).timestamp()
        return await ctx.reply(f"<t:{int(epoch)}:R>")

    @commands.command(pass_context=True)
    @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def create_lobby(self, ctx: commands.Context, lobby_name: str, lobby_start: str, invite_link: str, guild: int, desc: str, author: discord.Member = None, ):
        # User-host name
        if author is None:
            author = ctx.author
        # Start date
        timezone = {"CET": tz.gettz('EU/Central')}  # not sure if it works
        epoch = parser.parse(lobby_start, tzinfos=timezone).timestamp()
        # Invite link
        lobby_embed = discord.Embed(title=lobby_name, colour=discord.Colour.gold())
        lobby_embed.add_field(name=f"`Hosted by:`", value=f"<@{author.id}>")
        lobby_embed.add_field(name="`Start:`", value=f"<t:{int(epoch)}:R>\n<t:{int(epoch)}:f>")
        lobby_embed.add_field(name="`Discord invite:`", value=invite_link)
        lobby_embed.add_field(name="`Guild:`", value=ctx.guild)
        lobby_embed.add_field(name="`Schedule:`", value="Tuesdays, 19:00 - 19:01")
        lobby_embed.add_field(name="`Players to start:`", value="9")
        lobby_embed.add_field(name="`Description:`", value=desc, inline=False)
        lobby_embed.set_thumbnail(url=ctx.guild.icon_url)
        return await ctx.reply(embed=lobby_embed)


def setup(bot):
    bot.add_cog(LobbyFinderModule(bot))
