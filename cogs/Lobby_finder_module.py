import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
from discord import Webhook, AsyncWebhookAdapter  # Importing discord.Webhook and discord.AsyncWebhookAdapter
import sqlite3 as sl  # SQLite database
from dateutil import parser, tz  # Epoch time converter
import re  # RegEx

import config  # Global settings


class LobbyFinderModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO Commands to edit lobby information
    # TODO Introduce protecction against spammers. Possibly: long cooldown for each user / whitelist
    # TODO Command to report inappropriate lobby listing / blacklist. Webhook?
    # TODO Make more checks for correctness of input
    # TODO Make documentation/ help command
    # TODO Check if everything is fine, if retrieving information by id (user_id, guild_id and it's not cached) is fine

    @commands.command(pass_context=True)
    @commands.cooldown(1, config.cd_long_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def create_lobby(self, ctx: commands.Context, lobby_name: str, lobby_start: str, invite_link: str,
                           desc: str = "No data.", schedule: str = "No data.", num_players: int = -1,
                           author: discord.Member = None):
        # User-host name
        if author is None:
            author = ctx.author
        # Start date
        timezone = {"CET": tz.gettz('EU/Central')}  # not sure if it works
        epoch = parser.parse(lobby_start, tzinfos=timezone).timestamp()
        # Check if Discord invite link is valid
        match = re.search("(?:https?://)?discord(?:(?:app)?\.com/invite|\.gg)/?[a-zA-Z0-9]+/?", invite_link)
        if not match:
            return await ctx.reply("Couldn't recognise discord invite. Try another invite link.")

        print("oops", invite_link[len(invite_link):invite_link.find("/", -1, 0):])
        # Check whether number of players to start was passed
        if num_players <= 0:
            num_players = "Not specified"
        # Visibility
        visibility = "Local"
        # Embed
        lobby_embed = discord.Embed(title=lobby_name, colour=discord.Colour.dark_blue())
        lobby_embed.add_field(name=f"`Hosted by:`", value=f"<@{author.id}>")
        lobby_embed.add_field(name="`Start:`", value=f"<t:{int(epoch)}:R>\n<t:{int(epoch)}:f>")
        lobby_embed.add_field(name="`Discord invite:`", value=invite_link)
        lobby_embed.add_field(name="`Visibility:`", value=visibility)
        lobby_embed.add_field(name="`Guild:`", value=self.bot.get_guild(ctx.guild.id).name)
        lobby_embed.add_field(name="`Schedule:`", value=schedule)
        lobby_embed.add_field(name="`Players to start:`", value=num_players)
        lobby_embed.add_field(name="`Description:`", value=desc, inline=False)
        lobby_embed.set_thumbnail(url=self.bot.user.avatar_url)

        # Save in database
        sql_connection = sl.connect("Goose.db")
        sql_connection.execute(
            "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name));")

        if len(sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE lobby_name = '{lobby_name}' AND is_active = 1").fetchall()) != 0:
            return await ctx.reply("Multiplayer lobby with this name already exists. Try another name.")
        sql_connection.execute(
            "INSERT OR IGNORE INTO MP_LOBBIES (guild_id, lobby_name, host_name, start_time_epoch, discord_invite, schedule, minimum_players, description, author_id, is_active, global_visibility) VALUES (?,?,?,?,?,?,?,?,?,1,?)",
            (ctx.guild.id, lobby_name, author.id, epoch, invite_link, schedule, num_players, desc, ctx.author.id,
             "Local"))
        sql_connection.commit()
        sql_connection.close()
        # Webhook and reply
        webhook = Webhook.from_url(config.webhookMPLobbies, adapter=AsyncWebhookAdapter(
            self.bot.session))  # Initializing webhook with AsyncWebhookAdapter
        await ctx.reply(embed=lobby_embed)
        return await webhook.send(embed=lobby_embed, username="Goose Overseer")  # Executing webhook.

    @commands.command(pass_context=True)
    @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def active_lobbies(self, ctx: commands.Context):
        """Send embed with information about all active lobbies at the moment."""
        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        sql_connection.execute(
            "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name));")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id= {ctx.guild.id}").fetchall()) == 0:
            return await ctx.reply(f"No active lobbies at the moment.")
        sql_connection.close()
        # Embed
        message = f'Try something like `{config.prefix}lobby "golden goose mp"` to find out more about specified lobby.'
        active_lobbies_embed = discord.Embed(title=f"{ctx.guild.name} lobbies.", description=message,
                                             colour=discord.Colour.dark_blue())
        for lobby in data:
            short_desc = f"Hosted by: <@{lobby[2]}>\nStart: <t:{lobby[3]}:f>"
            active_lobbies_embed.add_field(name=f"`{lobby[1]}`", value=short_desc, inline=False)
        return await ctx.reply(embed=active_lobbies_embed)

    @commands.command(pass_context=True)
    @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def lobby(self, ctx: commands.Context, lobby_name: str):
        """Send embed with information about specific lobby."""
        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        sql_connection.execute(
            "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name));")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND lobby_name LIKE '{lobby_name}'").fetchall()) == 0:
            return await ctx.reply(f"No lobbies with `{lobby_name}` name found.")
        else:
            data = data[0]
        sql_connection.close()

        # Embed
        retrieved_lobby_embed = discord.Embed(title=data[1], colour=discord.Colour.dark_blue())
        retrieved_lobby_embed.add_field(name=f"`Hosted by:`", value=f"<@{data[2]}>")
        retrieved_lobby_embed.add_field(name="`Start:`", value=f"<t:{data[3]}:R>\n<t:{data[3]}:f>")
        retrieved_lobby_embed.add_field(name="`Discord invite:`", value=data[4])
        retrieved_lobby_embed.add_field(name="`Visibility:`", value=data[10])
        retrieved_lobby_embed.add_field(name="`Guild:`", value=self.bot.get_guild(data[0]).name)
        retrieved_lobby_embed.add_field(name="`Schedule:`", value=data[5])
        retrieved_lobby_embed.add_field(name="`Players to start:`", value=data[6])
        retrieved_lobby_embed.add_field(name="`Description:`", value=data[7], inline=False)
        retrieved_lobby_embed.set_thumbnail(url=self.bot.user.avatar_url)

        return await ctx.reply(embed=retrieved_lobby_embed)

    @commands.command(pass_context=True)
    @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def delist_lobby(self, ctx: commands.Context, lobby_name: str):
        """Remove specified lobby from list of active lobbies."""
        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        sql_connection.execute(
            "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name));")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f"You are neither host nor creator of this lobby nor have `Administrator` permissions to de-list `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f"No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply("Error.")
        # Removal itself - set is_active to 0
        sql_connection.execute("UPDATE MP_LOBBIES SET is_active = 0 WHERE guild_id = ? AND lobby_name = ?",
                               (data[0], data[1]))
        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly de-listed lobby `{data[1]}`.")

    @commands.Cog.listener('on_guild_remove')
    async def check_lobbies(self, ctx):
        """De-list any lobbies that exist in bot database which he is not a member of.
        Procc's on any on_guild_remove event"""
        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT guild_id, lobby_name FROM MP_LOBBIES WHERE is_active = 1").fetchall()) == 0:
            sql_connection.close()
            return
        # If guild is from other place than goose guilds - set is_active to 0
        for guild in self.bot.guilds:
            for entry_guild in data:
                if entry_guild[0] != guild.id:
                    sql_connection.execute("UPDATE MP_LOBBIES SET is_active = 0 WHERE guild_id = ? AND lobby_name = ?",
                                           (entry_guild[0], entry_guild[1]))
        sql_connection.commit()
        sql_connection.close()
        return

    # @commands.command()
    # @commands.is_owner()
    # async def change_lobby_visibility(self, ctx: commands.Context, lobby_name: str, visibility_status: str):
    #     """Change lobby visibility to Global."""
    #     # Database info retrieval
    #     sql_connection = sl.connect("Goose.db")
    #     sql_connection.execute(
    #         "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name));")
    #     if len(data := sql_connection.execute(
    #             f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
    #         data = data[0]
    #     elif len(data) == 0:
    #         return await ctx.reply(f"No lobbies with `{lobby_name}` name found.")
    #     else:
    #         return await ctx.reply("Error.")
    #     # changing global_visibility
    #     sql_connection.execute(f"UPDATE MP_LOBBIES SET global_visibility = '{visibility_status.lower().capitalize()}' WHERE guild_id = ? AND lobby_name = ?",
    #                            (data[0], data[1]))
    #     sql_connection.commit()
    #     sql_connection.close()
    #
    #     return await ctx.reply(f"Successfuly de-listed lobby `{data[1]}`.")


def setup(bot):
    bot.add_cog(LobbyFinderModule(bot))
