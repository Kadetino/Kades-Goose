import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import datetime  # until what time timeout lasts
import sqlite3 as sl  # SQLite database
import random  # percentages for duels

from config import prefix, cd_commands  # Global settings


class DuelModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO Make better documentation/ help command
    # TODO Make check for whether the user with incoming timeout already is timed out
    # to prevent people from dodging long(critical) timeouts. Stats still should be edited.
    # TODO make improvements to ranking system
    async def timeout_user(self, *, user_id: int, guild_id: int, until):
        """API request to timeout mentioned user in specific guild. Returns 'True' on success, 'False' on failure."""

        headers = {"Authorization": f"Bot {self.bot.http.token}"}
        url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}"
        timeout = (datetime.datetime.utcnow() + datetime.timedelta(minutes=until)).isoformat()
        json = {'communication_disabled_until': timeout}
        async with self.bot.session.patch(url, json=json, headers=headers) as session:
            if session.status in range(200, 299):
                return True
            return False

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def duel(self, ctx: commands.Context, member: discord.Member):
        # Init
        sql_connection = sl.connect('Goose.db')
        sql_connection.execute(
            "INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,0)",
            (ctx.guild.id, ctx.author.id))
        sql_connection.execute(
            "INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,0)",
            (ctx.guild.id, member.id))
        # Chances
        success_chance = random.randint(0, 100)
        critical_failure_chance = random.randint(0, 100)
        # Timeout duration
        default_punish_time = 1
        critical_failure_punish_time = 30
        # Other
        protectedusers = [231388394360537088, 912349700416479292]
        # Voice check
        voice_state_defender = member.voice
        voice_state_attacker = ctx.author.voice
        if voice_state_attacker is not None or voice_state_defender is not None:
            sql_connection.commit()
            sql_connection.close()
            return await ctx.reply(f"At least one of the duel participants is in voice chat.\n\nDuel cancelled.")
        # Both agreed to duel (generally speaking)
        def_consent = sql_connection.execute("SELECT opt_out FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                                             (ctx.guild.id, member.id)).fetchone()
        atk_consent = sql_connection.execute("SELECT opt_out FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                                             (ctx.guild.id, ctx.author.id)).fetchone()
        if atk_consent[0] == 1 or def_consent[0] == 1:
            sql_connection.commit()
            sql_connection.close()
            return await ctx.reply(
                f"At least one of the duel participants refuses to duel.\n`{prefix}duelOn` to enable duels; `{prefix}duelOff` to forbid them.\n\nDuel cancelled.")

        # Duel!
        if member.id in protectedusers:  # Kade and Goose never lose
            muted_user = ctx.author
            winner_user = member
            handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=default_punish_time)
            await ctx.reply(f"{muted_user} loses.")
        elif success_chance <= 66 and voice_state_defender is None:  # Attacker wins.
            muted_user = member
            winner_user = ctx.author
            handshake = await self.timeout_user(user_id=member.id, guild_id=ctx.guild.id, until=default_punish_time)
            await ctx.reply(f"{muted_user} loses.")
        else:  # Attacker loses
            muted_user = ctx.author
            winner_user = member
            if critical_failure_chance <= 97:  # Critical failure check
                handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id,
                                                    until=default_punish_time)
                await ctx.reply(f"{muted_user} loses.")
            else:
                handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id,
                                                    until=critical_failure_punish_time)
                await ctx.reply(f"{muted_user} shotguns himself.")

        if handshake:
            print(f"{ctx.guild.name} - Successfully timed out {muted_user} in {ctx.author} vs {member} fight.")
        else:
            print(
                f"{ctx.guild.name} - Something went wrong: couldn't time out {muted_user} in {ctx.author} vs {member} fight.")

        if not ctx.author.bot and not member.bot and member.id != ctx.author.id:
            sql_connection.execute("UPDATE DUELDATA SET loses = loses + 1 WHERE guild_id = ? AND user_id = ?",
                                   (ctx.guild.id, muted_user.id))
            sql_connection.execute("UPDATE DUELDATA SET wins = wins + 1 WHERE guild_id = ? AND user_id = ?",
                                   (ctx.guild.id, winner_user.id))
        # save changes
        sql_connection.commit()
        sql_connection.close()

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def duelOn(self, ctx: commands.Context):
        """Set 'opt_out' field in database to '0'. Enable participation in duels."""

        # Connect
        con = sl.connect('Goose.db')
        con.execute("INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,0)",
                    (ctx.guild.id, ctx.author.id))
        # Edit existing value
        con.execute("UPDATE DUELDATA SET opt_out = 0 WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
        # Save changes and close connection
        con.commit()
        con.close()
        # Notify user about changing his participation in duels
        return await ctx.message.add_reaction(u"\u2705")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def duelOff(self, ctx: commands.Context):
        """Set 'opt_out' field in database to '1'. Disable participation in duels."""

        # Connect
        con = sl.connect('Goose.db')
        # If user wasn't in the database before
        con.execute("INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,1)",
                    (ctx.guild.id, ctx.author.id))
        # Edit existing value
        con.execute("UPDATE DUELDATA SET opt_out = 1 WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
        # Save changes and close connection
        con.commit()
        con.close()
        # Notify user about changing his participation in duels
        return await ctx.message.add_reaction(u"\u2705")

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def duelstats(self, ctx: commands.Context, member: discord.Member = None):
        # Init
        con = sl.connect('Goose.db')
        if member is None:
            member = ctx.author
        con.execute("INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,0)",
                    (ctx.guild.id, member.id))
        # Retrieve wins
        data = con.execute("SELECT wins FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                           (ctx.guild.id, member.id)).fetchone()
        wins = data[0]
        # Retrive losses
        data = con.execute("SELECT loses FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                           (ctx.guild.id, member.id)).fetchone()
        losses = data[0]
        # Retrive participation
        data = con.execute("SELECT opt_out FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                           (ctx.guild.id, member.id)).fetchone()
        optout = "Duels forbidden" if data[0] == 1 else "Duels allowed"
        # Close connection
        con.commit()
        con.close()
        # Retrive winrate
        try:
            winrate = round(wins / losses, 2)
        except ZeroDivisionError:
            winrate = "NaN"
        # Rank
        rank_selection = [(10, "Copper"), (20, "Bronze"), (30, "Silver"), (45, "Gold"), (60, "Platinum"),
                          (80, "Diamond")]
        rank = "NaN"
        e = (wins + losses) * 0.1
        if wins > losses:
            e += wins - losses
        for i in rank_selection:
            if e < i[0]:
                rank = i[1]
                break

        embed = discord.Embed(title=f"Duel stats for {member.name}", colour=discord.Colour.gold())
        embed.add_field(name="Wins", value=str(wins))
        embed.add_field(name="Losses", value=str(losses))
        embed.add_field(name="W/L Ratio", value=str(winrate))
        embed.add_field(name="Participation", value=str(optout))
        embed.add_field(name="Rank", value=f"{rank}")
        embed.set_thumbnail(url=member.avatar_url)

        await ctx.reply(embed=embed)

    @commands.command(pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def duelHelp(self, ctx: commands.Context):
        embed = discord.Embed(title="All commands for dueling",
                              colour=discord.Colour.gold())
        embed.add_field(name=f"`{prefix}duel @someone`",
                        value=f"Duel person of your choice.",
                        inline=False)
        embed.add_field(name=f"`{prefix}duelstats @someone`",
                        value=f"Duel stats for yourself or person of your choice.",
                        inline=False)
        embed.add_field(name=f"`{prefix}duelOn`",
                        value="Enable participation in duels.",
                        inline=False)
        embed.add_field(name=f"`{prefix}duelOff`",
                        value="Disable participation in duels.",
                        inline=False)

        return await ctx.reply(embed=embed)

    @commands.command(name="duelboard", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def top_duelists(self, ctx: commands.Context):
        """Display top 10 duelists on this server. Sorted by winrate"""
        # Init
        con = sl.connect('Goose.db')
        # Get data and close
        data = con.execute(
            f"select user_id, wins, loses from DUELDATA where guild_id = {ctx.guild.id} order by wins desc limit 10").fetchall()
        con.close()
        # Check if data is empty
        if len(data) == 0:
            return await ctx.reply("Nothing to show.")
        # Calculate winrate
        storage = []
        for line in data:
            # Check for ZeroDivisionError
            try:
                winrate = round(line[1] / line[2], 2)
            except ZeroDivisionError:
                winrate = 0
            # Get user by his id
            user = self.bot.get_user(line[0])
            # If getting user failed
            if user is None:
                continue
            # Adding value to storage
            storage.append((f"{user.name}#{user.discriminator}", line[1], line[2], winrate))
        # Sort storage for leaderboard
        storage.sort(key=lambda y: y[3], reverse=True)
        # Discord embed
        embed = discord.Embed(title=f"Top 10 {ctx.guild.name} Duelists", colour=discord.Colour.gold())
        for i in range(len(storage)):
            # Check if m
            if i == 10:
                break

            # Start adding fields
            if i == 0:
                embed.add_field(name=f":first_place: {storage[i][0]}",
                                value=f"Wins: {storage[i][1]} | Losses: {storage[i][2]} | Winrate: {storage[i][3]}",
                                inline=False)
            elif i == 1:
                embed.add_field(name=f":second_place: {storage[i][0]}",
                                value=f"Wins: {storage[i][1]} | Losses: {storage[i][2]} | Winrate: {storage[i][3]}",
                                inline=False)
            elif i == 2:
                embed.add_field(name=f":third_place: {storage[i][0]}",
                                value=f"Wins: {storage[i][1]} | Losses: {storage[i][2]} | Winrate: {storage[i][3]}",
                                inline=False)
            else:
                embed.add_field(name=f"`#{i + 1}` {storage[i][0]}",
                                value=f"Wins: {storage[i][1]} | Losses: {storage[i][2]} | Winrate: {storage[i][3]}",
                                inline=False)
        embed.set_thumbnail(url=ctx.guild.icon_url)

        return await ctx.reply(embed=embed)


def setup(bot):
    sql_connection = sl.connect('Goose.db')
    sql_connection.execute(
        "CREATE TABLE IF NOT EXISTS DUELDATA (guild_id int, user_id int, wins int, loses int, opt_out int, PRIMARY KEY (guild_id, user_id))")
    sql_connection.close()
    bot.add_cog(DuelModule(bot))
