import re  # RegEx
import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
from dateutil import parser, tz  # Epoch time converter

import config  # Global settings


class LobbyFinderModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


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
    async def create_lobby_embed(self, ctx: commands.Context, lobby_name: str, lobby_start: str, invite_link: str, desc: str, schedule: str, num_players: int = -1, author: discord.Member = None):
        # User-host name
        if author is None:
            author = ctx.author
        # Start date
        timezone = {"CET": tz.gettz('EU/Central')}  # not sure if it works
        epoch = parser.parse(lobby_start, tzinfos=timezone).timestamp()
        # Check if Discord invite link is valid
        match = re.search("(?:https?://)?discord(?:(?:app)?\.com/invite|\.gg)/?[a-zA-Z0-9]+/?", invite_link)
        if not match:
            invite_link = "Invalid link."
        # Check whether number of players to start was passed
        if num_players <= 0:
            num_players = "Not specified"

        # Embed
        lobby_embed = discord.Embed(title=lobby_name, colour=discord.Colour.gold())
        lobby_embed.add_field(name=f"`Hosted by:`", value=f"<@{author.id}>")
        lobby_embed.add_field(name="`Start:`", value=f"<t:{int(epoch)}:R>\n<t:{int(epoch)}:f>")
        lobby_embed.add_field(name="`Discord invite:`", value=invite_link)
        lobby_embed.add_field(name="`Guild:`", value=ctx.guild)
        lobby_embed.add_field(name="`Schedule:`", value=schedule)
        lobby_embed.add_field(name="`Players to start:`", value=num_players)
        lobby_embed.add_field(name="`Description:`", value=desc, inline=False)
        lobby_embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.reply(embed=lobby_embed)
        return lobby_embed


def setup(bot):
    bot.add_cog(LobbyFinderModule(bot))
