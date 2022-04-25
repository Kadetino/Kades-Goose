import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
from discord import Webhook, AsyncWebhookAdapter  # Importing discord.Webhook and discord.AsyncWebhookAdapter
import sqlite3 as sl  # SQLite database
import time  # Epoch time
from dateutil import parser, tz  # Epoch time converter
import re  # RegEx

from config import cd_commands, prefix, cd_long_commands, webhookMPLobbies  # Global settings


class LobbyFinderModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO Command to report inappropriate lobby listing / blacklist.
    # TODO Command to request changing visibility to global - maybe implement partial checking without human intervention
    # TODO Make documentation/ help command
    # TODO make creating lobbies less painful
    # TODO Try breaking the code as malicious discord user
    # TODO local_lobbies and global_lobbies: limit on how many lobbies are shown at the given moment.
    # TODO you can't pass ' or " characters in strings. Feature or bug?

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_long_commands, commands.BucketType.user)
    @commands.guild_only()
    async def create_lobby(self, ctx: commands.Context, lobby_name: str, lobby_start: str,
                           invite_link: str = "No link.",
                           desc: str = "No data.", schedule: str = "No data.", num_players: int = -1,
                           author: discord.Member = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # User-host name
        if author is None:
            author = ctx.author

        # Start date
        timezone = {"CET": tz.gettz('EU/Central')}  # not sure if it works
        epoch = parser.parse(lobby_start, tzinfos=timezone).timestamp()
        epoch_timestamp_right_now = int(time.time())
        if epoch_timestamp_right_now > epoch:
            return await ctx.reply(f":warning: You can't create lobbies in the past.")

        # Check if Discord invite link is valid
        # Discord invite links with more than 55 characters are extremely suspicious
        if invite_link != "No link." and not len(invite_link) > 55:
            match = re.search("(?:https?://)?discord(?:(?:app)?\.com/invite|\.gg)/?[a-zA-Z0-9]+/?", invite_link)
            if not match:
                await ctx.reply(":warning: Couldn't recognise discord invite.")
                invite_link = "No link."
            else:
                # Send warning if discord invite might be invalid
                letters_after_invite = invite_link[invite_link.find("discord")::]
                letters_after_invite = letters_after_invite[letters_after_invite.find("/") + 1::]
                if len(letters_after_invite) < 10:
                    await ctx.reply(
                        ":warning: Warning: check your discord invite link. Your invite might have expiration timer.")
                elif len(letters_after_invite) > 10:
                    await ctx.reply(":warning: Warning: check your discord invite link. Your invite might be invalid.")
        elif len(invite_link) > 55:
            await ctx.reply(":warning: Invalid Discord invite. Please, use shorter invite links.")
            invite_link = "No link."
        else:
            invite_link = "No link."

        # Check whether number of players to start was passed
        if num_players <= 0:
            num_players = "Not specified"

        # Schedule
        if len(schedule) > 49 or schedule == "":
            await ctx.reply(":warning: Error. Please, use less than 50 characters for schedule.")
            schedule = "No data."

        # Description
        if len(desc) > 199 or desc == "":
            await ctx.reply(":warning: Error. Please, use less than 200 characters for schedule.")
            desc = "No data."

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
        lobby_embed.add_field(name="`Lobby created by:`", value=f"<@{ctx.author.id}>")
        lobby_embed.add_field(name="`Description:`", value=desc, inline=False)
        lobby_embed.set_thumbnail(url=self.bot.user.avatar_url)

        # Save in database
        sql_connection = sl.connect("Goose.db")
        if len(sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE lobby_name LIKE '{lobby_name}' AND is_active = 1 AND guild_id = {ctx.guild.id}").fetchall()) != 0:
            return await ctx.reply(
                ":warning: Multiplayer lobby with this name already exists. Try creating another lobby with different name.")
        sql_connection.execute(
            "INSERT OR IGNORE INTO MP_LOBBIES (guild_id, lobby_name, host_name, start_time_epoch, discord_invite, schedule, minimum_players, description, author_id, is_active, global_visibility) VALUES (?,?,?,?,?,?,?,?,?,1,?)",
            (ctx.guild.id, lobby_name, author.id, epoch, invite_link, schedule, num_players, desc, ctx.author.id,
             "Local"))
        sql_connection.commit()
        sql_connection.close()

        # Webhook and reply
        webhook = Webhook.from_url(webhookMPLobbies, adapter=AsyncWebhookAdapter(
            self.bot.session))  # Initializing webhook with AsyncWebhookAdapter
        await ctx.reply(embed=lobby_embed)
        return await webhook.send(embed=lobby_embed, username="Goose Overseer")  # Executing webhook.

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def local_lobbies(self, ctx: commands.Context):
        """Send embed with information about all active lobbies at the moment."""
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id= {ctx.guild.id}").fetchall()) == 0:
            return await ctx.reply(f"No local lobbies at the moment.")
        sql_connection.close()

        # Embed
        active_lobbies_embed = discord.Embed(title=f"{ctx.guild.name} lobbies.",
                                             description=f'Try something like `{prefix}lobby "golden goose mp"` to find out more about specified lobby.',
                                             colour=discord.Colour.dark_blue())
        for lobby in data:
            short_desc = f"Hosted by: <@{lobby[2]}>\nStart: <t:{lobby[3]}:f> | <t:{lobby[3]}:R>"
            active_lobbies_embed.add_field(name=f"`{lobby[1]}`", value=short_desc, inline=False)

        return await ctx.reply(embed=active_lobbies_embed)

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def global_lobbies(self, ctx: commands.Context):
        """Send embed with information about all active global lobbies at the moment."""
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND global_visibility = 'Global'").fetchall()) == 0:
            return await ctx.reply(f"No global lobbies at the moment.")
        sql_connection.close()
        # Embed
        active_lobbies_embed = discord.Embed(title=f"Global lobbies.",
                                             description=f'Try something like `{prefix}globby "golden goose mp"` to find out more about specified lobby.',
                                             colour=discord.Colour.dark_blue())
        for lobby in data:
            short_desc = f"Hosted by: <@{lobby[2]}>\nStart: <t:{lobby[3]}:f> | <t:{lobby[3]}:R>\nGuild: {self.bot.get_guild(lobby[0]).name}"
            active_lobbies_embed.add_field(name=f"`{lobby[1]}`", value=short_desc, inline=False)

        return await ctx.reply(embed=active_lobbies_embed)

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def lobby(self, ctx: commands.Context, lobby_name: str):
        """Send embed with information about specific lobby."""
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 0:
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
        retrieved_lobby_embed.add_field(name="`Lobby created by:`", value=f"<@{data[8]}>")
        retrieved_lobby_embed.add_field(name="`Description:`", value=data[7], inline=False)
        retrieved_lobby_embed.set_thumbnail(url=self.bot.user.avatar_url)

        return await ctx.reply(embed=retrieved_lobby_embed)

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def globby(self, ctx: commands.Context, lobby_name: str):
        """Send embed with information about specific global lobby."""
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND global_visibility = 'Global' AND lobby_name LIKE '{lobby_name}'").fetchall()) == 0:
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
        retrieved_lobby_embed.add_field(name="`Lobby created by:`", value=f"<@{data[8]}>")
        retrieved_lobby_embed.add_field(name="`Description:`", value=data[7], inline=False)
        retrieved_lobby_embed.set_thumbnail(url=self.bot.user.avatar_url)

        return await ctx.reply(embed=retrieved_lobby_embed)

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def delist_lobby(self, ctx: commands.Context, lobby_name: str):
        """Remove specified lobby from list of active lobbies."""
        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        sql_connection.execute(
            "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name));")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
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
    async def check_lobbies(self):
        """De-list any lobbies that exist in bot database which are from the servers' bot is not a member of.
        Procc's on any on_guild_remove event"""
        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT guild_id, lobby_name, start_time_epoch FROM MP_LOBBIES WHERE is_active = 1").fetchall()) == 0:
            sql_connection.close()
            return

        # If guild is from other place than goose guilds or older than 1 day - set is_active to 0
        epoch_timestamp_right_now = int(time.time())
        for guild in self.bot.guilds:
            for entry_guild in data:
                if entry_guild[0] != guild.id or epoch_timestamp_right_now >= entry_guild[2] + 1 * 24 * 3600:
                    sql_connection.execute("UPDATE MP_LOBBIES SET is_active = 0 WHERE guild_id = ? AND lobby_name = ?",
                                           (entry_guild[0], entry_guild[1]))

        sql_connection.commit()
        sql_connection.close()
        return

    @commands.command()
    @commands.is_owner()
    async def change_lobby_visibility(self, ctx: commands.Context, lobby_name: str, visibility_status: str,
                                      guild_id: int):
        """Change lobby visibility to Global. Only owners can execute this command."""
        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        sql_connection.execute(
            "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name));")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND lobby_name LIKE '{lobby_name}' AND guild_id = {guild_id}").fetchall()) == 1:
            data = data[0]
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Check if visibility is either "Local" or "Global"
        if visibility_status == "local" or visibility_status == "global":
            visibility_status = visibility_status.capitalize()
        elif visibility_status != "Global" and visibility_status != "Local":
            return await ctx.reply(f":warning: Incorrect visibility_input: it should be either `Local` or `Global`.")

        # Changing global_visibility
        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET global_visibility = '{visibility_status.lower().capitalize()}' WHERE guild_id = {guild_id} AND lobby_name = '{data[1]}'")
        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(
            f"Successfuly changed `{data[1]}` lobby visibility on `{self.bot.get_guild(guild_id).name}` to `{visibility_status}`.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def edit_lobby_description(self, ctx: commands.Context, lobby_name: str = None, target_field: str = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Check if there was any input
        if (lobby_name is None and target_field is None) or target_field == "":
            message = f"You can edit lobby description with this command.\n\nExample usage: `{prefix}edit_lobby_description \"golden goose\" \"my new description.\"`"
            return await ctx.reply(message)
        elif target_field is None:
            return

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]  # Convert List to tuple
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f":warning: You are neither host nor creator of this lobby nor have `Administrator` permissions to edit `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Processing input data
        if len(target_field) > 199:
            return await ctx.reply(":warning: Error. Please, use less than 200 characters for schedule.")
        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET description = '{target_field}' WHERE guild_id = ? AND lobby_name = ?",
            (data[0], data[1]))

        # Change global_visibilty to "Local" - because security reasons
        if data[10] == "Global":
            sql_connection.execute(
                "UPDATE MP_LOBBIES SET global_visibility = 'Local' WHERE guild_id = ? AND lobby_name = ?",
                (data[0], data[1]))
            await ctx.reply(
                f":warning: Changed lobby visibility from `Global` to `Local` as security measure.\nPlease, request changing visibility again.")

        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly edited description of `{data[1]}`.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def edit_lobby_schedule(self, ctx: commands.Context, lobby_name: str = None, target_field: str = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Check if there was any input
        if (lobby_name is None and target_field is None) or target_field == "":
            message = f"You can edit lobby schedule description with this command.\n\nExample usage: `{prefix}edit_lobby_schedule \"golden goose\" \"Saturday: 20:00 - 23:00 CET\"`"
            return await ctx.reply(message)
        elif target_field is None:
            return

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]  # Convert List to tuple
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f":warning: You are neither host nor creator of this lobby nor have `Administrator` permissions to edit `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Processing input data
        if len(target_field) > 49:
            return await ctx.reply(":warning: Error. Please, use less than 50 characters for schedule.")
        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET schedule = '{target_field}' WHERE guild_id = ? AND lobby_name = ?",
            (data[0], data[1]))

        # Change global_visibilty to "Local" - because security reasons
        if data[10] == "Global":
            sql_connection.execute(
                "UPDATE MP_LOBBIES SET global_visibility = 'Local' WHERE guild_id = ? AND lobby_name = ?",
                (data[0], data[1]))
            await ctx.reply(
                f":warning: Changed lobby visibility from `Global` to `Local` as security measure.\nPlease, request changing visibility again.")

        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly edited schedule description of `{data[1]}`.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def edit_lobby_host(self, ctx: commands.Context, lobby_name: str = None,
                              target_member: discord.Member = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Check if there was any input
        if lobby_name is None and target_member is None:
            message = f"You can edit lobby host with this command.\n\nExample usage: `{prefix}edit_lobby_host \"golden goose\" @someone`"
            return await ctx.reply(message)
        elif target_member is None:
            return

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]  # Convert List to tuple
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f":warning: You are neither host nor creator of this lobby nor have `Administrator` permissions to edit `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Processing input data
        if target_member.bot:
            return await ctx.reply(":warning: Error. Please, do not make bots responsible for lobbies.")
        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET host_name = {target_member.id} WHERE guild_id = ? AND lobby_name = ?",
            (data[0], data[1]))

        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly edited host of `{data[1]}`.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def edit_lobby_invite(self, ctx: commands.Context, lobby_name: str = None, target_field: str = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Check if there was any input
        if (lobby_name is None and target_field is None) or target_field == "":
            message = f"You can edit lobby discord invite with this command.\n\nExample usage: `{prefix}edit_lobby_host \"golden goose\" mydiscordinvite`"
            return await ctx.reply(message)
        elif target_field is None:
            return

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]  # Convert List to tuple
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f":warning: You are neither host nor creator of this lobby nor have `Administrator` permissions to edit `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Check if Discord invite link is valid
        if target_field is not None:
            # Discord invite links with more than 55 characters are extremely suspicious
            if len(target_field) > 55:
                sql_connection.close()
                return await ctx.reply(":warning: Please, use shorter invite links.")
            # Regex
            match = re.search("(?:https?://)?discord(?:(?:app)?\.com/invite|\.gg)/?[a-zA-Z0-9]+/?", target_field)
            if not match:
                sql_connection.close()
                return await ctx.reply(":warning: Couldn't recognise discord invite.")
            else:
                # Send warning if discord invite might be invalid
                letters_after_invite = target_field[target_field.find("discord")::]
                letters_after_invite = letters_after_invite[letters_after_invite.find("/") + 1::]
                if len(letters_after_invite) < 10:
                    await ctx.reply(
                        ":warning: Warning: check your discord invite link. Your invite might have expiration timer.")
                elif len(letters_after_invite) > 10:
                    await ctx.reply(
                        ":warning: Warning: check your discord invite link. Your invite might be invalid.")
        else:
            return

        # Change global_visibilty to "Local" - because security reasons
        if data[10] == "Global":
            sql_connection.execute(
                "UPDATE MP_LOBBIES SET global_visibility = 'Local' WHERE guild_id = ? AND lobby_name = ?",
                (data[0], data[1]))
            await ctx.reply(
                f":warning: Changed lobby visibility from `Global` to `Local` as security measure.\nPlease, request changing visibility again.")

        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET discord_invite = '{target_field}' WHERE guild_id = ? AND lobby_name = ?",
            (data[0], data[1]))

        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly edited discord invite of `{data[1]}`.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def edit_lobby_players(self, ctx: commands.Context, lobby_name: str = None, target_field: int = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Check if there was any input
        if lobby_name is None and target_field is None:
            message = f"You can edit lobby `Players to start` field with this command.\n\nExample usage: `{prefix}edit_lobby_players \"golden goose\" 7`"
            return await ctx.reply(message)
        elif target_field is None:
            return

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]  # Convert List to tuple
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f":warning: You are neither host nor creator of this lobby nor have `Administrator` permissions to edit `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Check if arguement is valid
        if target_field < 0:
            target_field = 0

        # Update
        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET minimum_players = {target_field} WHERE guild_id = ? AND lobby_name = ?",
            (data[0], data[1]))

        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly edited `Players to start` field of `{data[1]}`.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def edit_lobby_start(self, ctx: commands.Context, lobby_name: str = None, target_field: str = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Check if there was any input
        if (lobby_name is None and target_field is None) or target_field == "":
            message = f"You can edit lobby start date with this command.\n\nExample usage: `{prefix}edit_lobby_start \"golden goose\" \"01-01-2021 17:00\"`"
            return await ctx.reply(message)
        elif target_field is None:
            return

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]  # Convert List to tuple
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f":warning: You are neither host nor creator of this lobby nor have `Administrator` permissions to edit `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Processing input data
        timezone = {"CET": tz.gettz('EU/Central')}  # not sure if it works
        epoch = parser.parse(target_field, tzinfos=timezone).timestamp()
        epoch_timestamp_right_now = int(time.time())
        if epoch_timestamp_right_now > epoch:
            sql_connection.close()
            return await ctx.reply(f":warning: You can't create lobbies in the past.")

        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET start_time_epoch = '{epoch}' WHERE guild_id = ? AND lobby_name = ?",
            (data[0], data[1]))

        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly edited lobby start date of `{data[1]}`.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.user)
    @commands.guild_only()
    async def edit_lobby_name(self, ctx: commands.Context, lobby_name: str = None, target_field: str = None):
        # Remove outdated/invalid lobbies
        await self.check_lobbies()

        # Check if there was any input
        if (lobby_name is None and target_field is None) or target_field == "":
            message = f"You can edit lobby name with this command.\n\nExample usage: `{prefix}edit_lobby_start \"golden goose\" \"Crimson Goose\"`"
            return await ctx.reply(message)
        elif target_field is None:
            return

        # Database info retrieval
        sql_connection = sl.connect("Goose.db")
        if len(data := sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE is_active = 1 AND guild_id = {ctx.guild.id} AND lobby_name LIKE '{lobby_name}'").fetchall()) == 1:
            data = data[0]  # Convert List to tuple
            # Check if user has permissions to de-list this lobby: host, author or member with administator permissions
            if data[2] != ctx.author.id and data[8] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                return await ctx.reply(
                    f":warning: You are neither host nor creator of this lobby nor have `Administrator` permissions to edit `{lobby_name}` lobby.")
        elif len(data) == 0:
            return await ctx.reply(f":warning: No lobbies with `{lobby_name}` name found.")
        else:
            return await ctx.reply(":warning: Error.")

        # Processing input data
        if len(sql_connection.execute(
                f"SELECT * FROM MP_LOBBIES WHERE lobby_name LIKE '{target_field}' AND is_active = 1 AND guild_id = {ctx.guild.id}").fetchall()) != 0:
            return await ctx.reply(
                ":warning: Multiplayer lobby with this name already exists.")

        # Change global_visibilty to "Local" - because security reasons
        if data[10] == "Global":
            sql_connection.execute(
                "UPDATE MP_LOBBIES SET global_visibility = 'Local' WHERE guild_id = ? AND lobby_name = ?",
                (data[0], data[1]))
            await ctx.reply(
                f":warning: Changed lobby visibility from `Global` to `Local` as security measure.\nPlease, request changing visibility again.")

        sql_connection.execute(
            f"UPDATE MP_LOBBIES SET lobby_name = '{target_field}' WHERE guild_id = ? AND lobby_name = ?",
            (data[0], data[1]))

        sql_connection.commit()
        sql_connection.close()

        return await ctx.reply(f"Successfuly edited lobby name of `{data[1]}` to `{target_field}`.")


def setup(bot):
    sql_connection = sl.connect("Goose.db")
    sql_connection.execute(
        "CREATE TABLE IF NOT EXISTS MP_LOBBIES(guild_id int, lobby_name str, host_name int, start_time_epoch int, discord_invite str, schedule str, minimum_players int, description str,author_id int,is_active int, global_visibility str, primary key (guild_id, lobby_name))")
    sql_connection.commit()
    sql_connection.close()
    bot.add_cog(LobbyFinderModule(bot))
