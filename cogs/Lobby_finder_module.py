import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
from dateutil import parser  # Epoch time converter

import config  # Global settings


class Lobby:
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

    @commands.command(pass_context=True)
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
        epoch = parser.parse(date).timestamp()
        return await ctx.reply(f"<t:{int(epoch)}:R>")


def setup(bot):
    bot.add_cog(LobbyFinderModule(bot))
