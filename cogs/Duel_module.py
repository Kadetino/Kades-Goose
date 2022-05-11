import datetime  # until what time timeout lasts
import random  # percentages for duels
import sqlite3 as sl  # SQLite database

import discord  # Discord API wrapper
from discord import app_commands  # Slash commands
from discord.app_commands import Choice  # Slash command choices
from discord.ext import commands  # Discord BOT


class DuelModule(commands.GroupCog, name="duel"):
    def __init__(self, bot):
        self.bot = bot

    # TODO make improvements to ranking system

    @app_commands.command(name="fight", description="Вызвать пользователя на дуэль.")
    @app_commands.describe(member="Пользователь, кого вы хотите вызвать на дуэль.")
    async def duel(self, ctx: discord.Interaction, member: discord.Member):
        # Connect database
        sql_connection = sl.connect('Peacock.db')

        # Insert duelists information
        sql_connection.execute(
            "INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,1)",
            (ctx.guild.id, ctx.user.id))
        sql_connection.execute(
            "INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,1)",
            (ctx.guild.id, member.id))

        # Calculate chances
        success_chance = random.randint(0, 100)
        critical_failure_chance = random.randint(0, 100)

        # Timeout duration
        default_punish_time = 2
        critical_failure_punish_time = 30

        # Other
        protectedusers = [231388394360537088, 912349700416479292, 950687118986981416]
        did_crit_occur = False

        # Voice check
        voice_state_defender = member.voice
        voice_state_attacker = ctx.user.voice
        if voice_state_attacker is not None or voice_state_defender is not None:
            # Close
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Дуэль не состоялась",
                                        description=f"Хотя бы один из участников находится в голосовом чате.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            # Reply
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Both agreed to duel (generally speaking)
        def_consent = sql_connection.execute("SELECT opt_out FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                                             (ctx.guild.id, member.id)).fetchone()
        atk_consent = sql_connection.execute("SELECT opt_out FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                                             (ctx.guild.id, ctx.user.id)).fetchone()
        if atk_consent[0] == 1 or def_consent[0] == 1 or member.bot or ctx.user.bot:
            # Close
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Дуэль не состоялась",
                                        description=f"Хотя бы один из участников дуэли отказывается участвовать в ней.\nИспользуйте слэш-команду, чтобы поменять согласие на участие в дуэлях.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            # Reply
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Duel!
        # No timeouts for protected users
        if member.id in protectedusers:  # Kade and Goose never lose
            muted_user = ctx.user
            winner_user = member

        # Attacker wins - 66%
        elif success_chance <= 66 and voice_state_defender is None:
            muted_user = member
            winner_user = ctx.user

        # Attacker loses - 34%
        else:
            muted_user = ctx.user
            winner_user = member

            # Critical failure check
            if critical_failure_chance > 97:
                did_crit_occur = True

        # Reply embed
        reply_embed = discord.Embed(title=f"⚔️Дуэль: {ctx.user} vs {member}",
                                    description=f"<@{winner_user.id}> побеждает в дуэли против <@{muted_user.id}>!",
                                    colour=discord.Colour.gold())
        reply_embed.timestamp = datetime.datetime.utcnow()
        reply_embed.set_thumbnail(url=winner_user.avatar)
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)

        # Timeout loser
        if did_crit_occur:
            reply_embed.add_field(name="`Прочее:`",
                                  value=f"<@{muted_user.id}> был взорван гранатой.")
            timeout = datetime.datetime.now().astimezone() + datetime.timedelta(minutes=critical_failure_punish_time)
        else:
            timeout = datetime.datetime.now().astimezone() + datetime.timedelta(minutes=default_punish_time)

        # Timeout
        await muted_user.edit(timed_out_until=timeout)

        # Update win/loss information
        if not ctx.user.bot and not member.bot and member.id != ctx.user.id and not muted_user.is_timed_out():
            sql_connection.execute("UPDATE DUELDATA SET loses = loses + 1 WHERE guild_id = ? AND user_id = ?",
                                   (ctx.guild.id, muted_user.id))
            sql_connection.execute("UPDATE DUELDATA SET wins = wins + 1 WHERE guild_id = ? AND user_id = ?",
                                   (ctx.guild.id, winner_user.id))

        # Commit changes and close
        sql_connection.commit()
        sql_connection.close()

        # Reply
        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="status",
                          description="Поменять статус участия в дуэлях.")
    @app_commands.choices(parameter=[
        Choice(name='Разрешить участие в дуэлях', value="on"),
        Choice(name='Запретить участие в дуэлях', value="off")
    ])
    async def status(self, ctx: discord.Interaction, parameter: str):
        # Connect to database
        sql_connection = sl.connect('Peacock.db')
        sql_connection.execute(
            "INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,1)",
            (ctx.guild.id, ctx.user.id))

        # Add user if he wasn't in the database before
        sql_connection.execute(
            "INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,1)",
            (ctx.guild.id, ctx.user.id))

        # Change status - Duel status "on"
        if parameter == "on":
            # Edit existing value - Duel status "on"
            sql_connection.execute("UPDATE DUELDATA SET opt_out = 0 WHERE guild_id = ? AND user_id = ?",
                                   (ctx.guild.id, ctx.user.id))
            # Save changes and close connection
            sql_connection.commit()
            sql_connection.close()

            # Reply
            return await ctx.response.send_message(
                u"\u2705" + f" <@{ctx.user.id}>, вы дали своё согласие на участие в дуэлях.",
                ephemeral=False)
        elif parameter == "off":
            # Edit existing value - Duel status "off"
            sql_connection.execute("UPDATE DUELDATA SET opt_out = 1 WHERE guild_id = ? AND user_id = ?",
                                   (ctx.guild.id, ctx.user.id))
            # Save changes and close connection
            sql_connection.commit()
            sql_connection.close()

            # Reply
            return await ctx.response.send_message(
                u"\u2705" + f" <@{ctx.user.id}>, вы отозвали своё согласие на участие в дуэлях.",
                ephemeral=False)

        # Error?
        else:
            # Save changes and close connection
            sql_connection.commit()
            sql_connection.close()

            return await ctx.response.send_message("Error", ephemeral=True)

    @app_commands.command(name="profile", description="Просмотреть профиль.")
    @app_commands.describe(member="Пользователь, чей профиль вы хотите просмотреть.")
    async def duelstats(self, ctx: discord.Interaction, member: discord.Member = None):
        # Init
        sql_connection = sl.connect('Peacock.db')
        if member is None:
            member = ctx.user
        sql_connection.execute(
            "INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses, opt_out) VALUES (?,?,0,0,1)",
            (ctx.guild.id, member.id))
        # Retrieve wins
        data = sql_connection.execute("SELECT wins FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                                      (ctx.guild.id, member.id)).fetchone()
        wins = data[0]
        # Retrive losses
        data = sql_connection.execute("SELECT loses FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                                      (ctx.guild.id, member.id)).fetchone()
        losses = data[0]
        # Retrive participation
        data = sql_connection.execute("SELECT opt_out FROM DUELDATA WHERE guild_id = ? AND user_id = ?",
                                      (ctx.guild.id, member.id)).fetchone()
        optout = "Запрет на участие." if data[0] == 1 else "Участие разрешено."

        # Close connection
        sql_connection.commit()
        sql_connection.close()

        # Retrive winrate
        try:
            winrate = round(wins / losses, 2)
        except ZeroDivisionError:
            winrate = "NaN"
        # Rank
        rank_selection = [(10, "Медь"), (20, "Бронза"), (30, "Серебро"), (45, "Золото"), (60, "Платина"),
                          (80, "Алмаз")]
        rank = "NaN"
        e = (wins + losses) * 0.1
        if wins > losses:
            e += wins - losses
        for i in rank_selection:
            if e < i[0]:
                rank = i[1]
                break

        embed = discord.Embed(title=f"Статистика дуэлей {member.name}", colour=discord.Colour.gold())
        embed.add_field(name="Победы", value=str(wins))
        embed.add_field(name="Поражения", value=str(losses))
        embed.add_field(name="W/L", value=str(winrate))
        embed.add_field(name="Согласие", value=str(optout))
        embed.add_field(name="Ранг", value=f"{rank}")
        embed.set_thumbnail(url=member.avatar)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"{ctx.guild.name}",
                         icon_url=ctx.guild.icon)

        return await ctx.response.send_message(embed=embed)

    @app_commands.command(name="duelboard", description="Просмотреть топ 10 дуэлистов сервера.")
    async def top_duelists(self, ctx: discord.Interaction):
        # Init
        sql_connection = sl.connect('Peacock.db')

        # Get data and close
        data = sql_connection.execute(
            f"select user_id, wins, loses from DUELDATA where guild_id = {ctx.guild.id} order by wins desc limit 10").fetchall()
        sql_connection.close()

        # Check if data is empty
        if len(data) == 0:
            return await ctx.response.send_message("Нечего показывать", ephemeral=True)
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
            storage.append((f"{user}", line[1], line[2], winrate))
        # Sort storage for leaderboard
        storage.sort(key=lambda y: y[3], reverse=True)
        # Discord embed
        embed = discord.Embed(title=f"Топ 10 {ctx.guild.name} дуэлистов", colour=discord.Colour.gold())
        for i in range(len(storage)):
            # Check if m
            if i == 10:
                break

            # Start adding fields
            if i == 0:
                embed.add_field(name=f":first_place: {storage[i][0]}",
                                value=f"Победы: {storage[i][1]} | Поражения: {storage[i][2]} | W/L: {storage[i][3]}",
                                inline=False)
            elif i == 1:
                embed.add_field(name=f":second_place: {storage[i][0]}",
                                value=f"Победы: {storage[i][1]} | Поражения: {storage[i][2]} | W/L: {storage[i][3]}",
                                inline=False)
            elif i == 2:
                embed.add_field(name=f":third_place: {storage[i][0]}",
                                value=f"Победы: {storage[i][1]} | Поражения: {storage[i][2]} | W/L: {storage[i][3]}",
                                inline=False)
            else:
                embed.add_field(name=f"`#{i + 1}` {storage[i][0]}",
                                value=f"Победы: {storage[i][1]} | Поражения: {storage[i][2]} | W/L: {storage[i][3]}",
                                inline=False)
        embed.set_thumbnail(url=ctx.guild.icon)

        return await ctx.response.send_message(embed=embed, ephemeral=False)


async def setup(bot):
    sql_connection = sl.connect('Peacock.db')
    sql_connection.execute(
        "CREATE TABLE IF NOT EXISTS DUELDATA (guild_id int, user_id int, wins int, loses int, opt_out int, PRIMARY KEY (guild_id, user_id))")
    sql_connection.commit()
    sql_connection.close()
    await bot.add_cog(DuelModule(bot))
