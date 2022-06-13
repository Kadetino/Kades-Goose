import discord  # Discord API wrapper
from discord import app_commands  # Slash commands
from discord.app_commands import Choice  # Slash command choices
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
from random import randint  # Random number generation for economy
from config import prefix  # Global settings
from time import time  # Epoch timestamp
import datetime  # Shop - timeout

import localisation as loc


class peacockEconomyCog(commands.GroupCog, name="economy"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def on_message_give_peacocks(self, user_message: discord.message.Message):
        """Gain peacocks per sent message. Cooldown 10 seconds. Bonus points for using peacock emote."""
        # Checks and connecting database
        if user_message.author.bot or user_message.content.startswith(prefix):
            return
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (user_message.guild.id, user_message.author.id))

        # Check if there is message cooldown
        database_entry = sql_connection.execute(
            f"SELECT message_cooldown FROM ECONOMY WHERE guild_id = {user_message.guild.id} AND user_id = {user_message.author.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < database_entry + 10:
            return sql_connection.close()
        else:
            sql_connection.execute(
                f"UPDATE ECONOMY SET message_cooldown = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (user_message.guild.id, user_message.author.id))
            sql_connection.commit()

        # Amount of peacocks gained per message: bonus points for using specific emoji
        peacocks_gained = randint(0, 12)
        peacock_emote = "🦚"
        if peacock_emote in str(user_message.content):
            # Maybe needs balancing
            message_peacocks = str(user_message.content).count(peacock_emote)
            emote_multiplier = 2 if message_peacocks >= 3 else message_peacocks
            peacocks_gained += 3 * emote_multiplier

        # Update database entry
        sql_connection.execute(
            f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {peacocks_gained} WHERE guild_id = ? AND user_id = ?",
            (user_message.guild.id, user_message.author.id))

        # Commit and close
        sql_connection.commit()
        return sql_connection.close()

    @app_commands.command(name="profile", description="Просмотреть профиль.")
    @app_commands.describe(member="Пользователь, чей профиль вы хотите просмотреть.")
    async def display_user_profile(self, ctx: discord.Interaction, member: discord.Member = None):
        # Check if user argument was provided
        if member is None:
            member = ctx.user

        # Database connection
        sql_connection = sl.connect("Peacock.db")

        # Profile retrieval
        data = sql_connection.execute(
            f"SELECT cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}").fetchone()
        cooldown_data = sql_connection.execute(
            f"SELECT last_access, last_theft_attempt, daily_bonus, weekly_bonus, monthly_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}").fetchone()
        sql_connection.close()

        # Nothing found
        if data is None:
            return await ctx.response.send_message(f"<@{member.id}> не имеет профиля.", ephemeral=True)
        else:
            member_cookies = f"🦚 {data[0]}"
            bank_info = f"🦚 {data[1]} из {data[2] * 400}"
            upgrade_info = f"`{loc.upg1}`: {data[3]} уровень\n" \
                           f"`{loc.upg2}`: {data[4]} уровень\n" \
                           f"`{loc.upg3}`: {data[5]} уровень\n" \
                           f"`{loc.upg4}`: {data[6]} уровень\n" \
                           f"`{loc.upg5}`: {data[7]} уровень\n" \
                           f"`{loc.upg6}`: {data[8]} уровень\n" \
                           f"`{loc.upg7}`: {data[9]} уровень\n"
            total_info = f"~ 🦚 {data[0] + data[1]}"
            cooldown_info = ""
            # Work timer
            if cooldown_data[0] + 3600 * 2 < int(time()):
                cooldown_info += ", `/work`"
            # Daily bonus timer
            if cooldown_data[2] + 24 * 3600 < int(time()):
                cooldown_info += ", `/daily`"
            # Weekly bonus timer
            if cooldown_data[3] + 7 * 24 * 3600 < int(time()):
                cooldown_info += ", `/weekly`"
            # Monthly bonus timer
            if cooldown_data[3] + 30 * 24 * 3600 < int(time()):
                cooldown_info += ", `/monthly`"
            # Theft timer
            if cooldown_data[1] + 10 * 60 < int(time()):
                cooldown_info += ", `/steal`"

        # Reply embed
        reply_embed = discord.Embed(title=f"Профиль {member.name}",
                                    colour=discord.Colour.gold())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_thumbnail(url=member.avatar)
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        reply_embed.add_field(name=f"Кошелёк:", value=member_cookies, inline=False)
        reply_embed.add_field(name=f"Банк:", value=bank_info, inline=False)
        reply_embed.add_field(name=f"Улучшения:", value=upgrade_info, inline=False)
        reply_embed.add_field(name=f"Кошелёк+Банк:", value=total_info, inline=False)
        # Make cooldown_info fancy and add field
        if cooldown_info != "":
            cooldown_info = f"Вам доступны следующие награды: {cooldown_info[2::]}."
            reply_embed.add_field(name=f"Награды:", value=cooldown_info, inline=False)

        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="daily", description="Получить ежедневный бонус.")
    async def daily_bonus(self, ctx: discord.Interaction):
        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Check if there is message cooldown
        last_daily_bonus_received_epoch = sql_connection.execute(
            f"SELECT daily_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_daily_bonus_received_epoch + 24 * 3600:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Бонус дня",
                                        description=f"Вы уже получили свой ежедневный бонус. Вернитесь <t:{last_daily_bonus_received_epoch + 24 * 3600}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET daily_bonus = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + 400 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Бонус дня",
                                        description=f"Вы получили ежедневную награду в 🦚 400.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="weekly", description="Получить еженедельный бонус.")
    async def weekly_bonus(self, ctx: discord.Interaction):
        # Connecting database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Check if there is message cooldown
        last_weekly_bonus_received_epoch = sql_connection.execute(
            f"SELECT weekly_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_weekly_bonus_received_epoch + 7 * 24 * 3600:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Бонус недели",
                                        description=f"Вы уже получили свой еженедельный бонус. Вернитесь <t:{last_weekly_bonus_received_epoch + 7 * 24 * 3600}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET weekly_bonus = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + 750 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Бонус недели",
                                        description=f"Вы получили еженедельную награду в 🦚 750.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="monthly", description="Получить ежемесячный бонус.")
    async def monthly_bonus(self, ctx: discord.Interaction):
        # Connecting database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Check if there is message cooldown
        last_weekly_bonus_received_epoch = sql_connection.execute(
            f"SELECT monthly_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_weekly_bonus_received_epoch + 30 * 24 * 3600:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Бонус месяца",
                                        description=f"Вы уже получили свой ежемесячный бонус. Вернитесь <t:{last_weekly_bonus_received_epoch + 30 * 24 * 3600}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET monthly_bonus = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + 1500 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Бонус месяца",
                                        description=f"Вы получили ежемесячную награду в 🦚 1500.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="leaderboard", description="Просмотреть таблицу лидеров. Work in progress.")
    async def economyboard(self, ctx: discord.Interaction):
        # TODO view more than 10 entries. Buttons?
        # Connect to database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Get data and close
        data = sql_connection.execute(
            f"select user_id, cookie_counter, cookie_jar_storage, last_access, daily_bonus, weekly_bonus, monthly_bonus, last_theft_attempt from ECONOMY where guild_id = {ctx.guild.id}").fetchall()
        sql_connection.commit()
        sql_connection.close()

        # Check if data is empty
        if len(data) == 0:
            return await ctx.response.send_message("Nothing to show.", ephemeral=True)

        # Calculate total amount of peacocks
        storage = []  # place to store tuples
        author_entry = "Error"

        # Go through data
        for line in data:
            total_peacocks = line[1] + line[2]
            # Get user by his id
            user = self.bot.get_user(line[0])
            # If getting user failed
            if user is None:
                continue
            # Adding value to storage
            storage.append((f"{user}", total_peacocks, line[1], line[2]))

        # Sort storage for leaderboard
        storage.sort(key=lambda y: y[1], reverse=True)

        # Author stats
        for i in range(len(storage)):
            if storage[i][0] == str(ctx.user):
                author_entry = f"Ваша позиция: `#{i + 1}` {ctx.user}: 🦚 {storage[i][1]}"
                break

        # Discord embed
        embed = discord.Embed(title=f"{ctx.guild.name} leaderboard",
                              description=author_entry,
                              colour=discord.Colour.gold())
        for i in range(len(storage)):
            # Check if more than 10 entries already
            if i == 10:
                break

            # Start adding fields
            if i == 0:
                embed.add_field(name=f":first_place: {storage[i][0]}",
                                value=f"Всего: 🦚 {storage[i][1]}\nКошелёк: 🦚 {storage[i][2]}\nБанк: 🦚 {storage[i][3]}",
                                inline=False)
            elif i == 1:
                embed.add_field(name=f":second_place: {storage[i][0]}",
                                value=f"Всего: 🦚 {storage[i][1]}\nКошелёк: 🦚 {storage[i][2]}\nБанк: 🦚 {storage[i][3]}",
                                inline=False)
            elif i == 2:
                embed.add_field(name=f":third_place: {storage[i][0]}",
                                value=f"Всего: 🦚 {storage[i][1]}\nКошелёк: 🦚 {storage[i][2]}\nБанк: 🦚 {storage[i][3]}",
                                inline=False)
            else:
                embed.add_field(name=f"`#{i + 1}` {storage[i][0]}",
                                value=f"Всего: 🦚 {storage[i][1]}\nКошелёк: 🦚 {storage[i][2]}\nБанк: 🦚 {storage[i][3]}",
                                inline=False)

        # Embed: Icon and description on how it works
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.add_field(name=f"❓ Как это работает?",
                        value=f"Вы получаете 🦚 павлинов за отправленные сообщения и различные слэш-команды.",
                        inline=False)
        embed.timestamp = loc.moscow_timezone()
        embed.set_footer(text=f"{ctx.user}",
                         icon_url=ctx.user.avatar)

        return await ctx.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="give", description="Передать 🦚 другому пользователю. Комиссия 5% за перевод.")
    @app_commands.describe(member="Пользователь, который получит от вас 🦚.",
                           amount="Количество 🦚, которое вы переведёте.")
    async def transfer_peacocks(self, ctx: discord.Interaction, member: discord.Member, amount: int):
        # Checks if target is valid member
        if member.bot:  # Target is a bot
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Боты не люди.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        elif ctx.user.id == member.id:  # Target is yourself
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Вы не можете перевести самому себе.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Connection to database and retrieving authors peacocks
        sql_connection = sl.connect('Peacock.db')
        author_cookies = sql_connection.execute(
            f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Check if author has sufficien amount of peacocks
        if author_cookies < round(amount * 1.05) + 1:  # He doesn't have enough
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, у вас недостаточно 🦚 для перевода другому человеку.\nВы имеете 🦚 {author_cookies} в кошельке.\nВам необходимо иметь сумму перевода и заплатить 5% от неё как комиссию.",
                                        colour=discord.Colour.red())
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            # Close connection and reply
            sql_connection.close()

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:  # Author has enough
            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Успешный перевод",
                                        description=f"<@{member.id}> получил 🦚 {amount} от <@{ctx.user.id}>.\n\nКомиссия была 5% 🦚.",
                                        colour=discord.Colour.green())
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            # Add user to database if he wasn't there before
            sql_connection.execute(
                "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
                (ctx.guild.id, member.id))

            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            if round(amount * 0.05) == 0:
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - 1 WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
            else:
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {round(amount * 0.05)} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, member.id))
            sql_connection.commit()
            sql_connection.close()

            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="buy_upgrade", description="Купить одно улучшение за 🦚.")
    @app_commands.describe(upgrade="Улучшение, которые вы купите за 🦚")
    @app_commands.choices(upgrade=[
        Choice(name='Список стоимости покупки улучшений', value="help"),
        Choice(name='Банк', value="bank"),
        Choice(name=f'Улучшение 1 - {loc.upg1}', value="upgrade1"),
        Choice(name=f'Улучшение 2 - {loc.upg2}', value="upgrade2"),
        Choice(name=f'Улучшение 3 - {loc.upg3}', value="upgrade3"),
        Choice(name=f'Улучшение 4 - {loc.upg4}', value="upgrade4"),
        Choice(name=f'Улучшение 5 - {loc.upg5}', value="upgrade5"),
        Choice(name=f'Улучшение 6 - {loc.upg6}', value="upgrade6"),
        Choice(name=f'Улучшение 7 - {loc.upg7}', value="upgrade7"),
    ])
    async def buy_upgrade(self, ctx: discord.Interaction, upgrade: str):
        # Database connection
        sql_connection = sl.connect("Peacock.db")

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Upgrade - Bank
        if upgrade == "bank":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, cookie_jar_storage_level FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 200 * 2 ** upgrade_level

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень банка.\nВаш кошелёк: 🦚 {author_cookies}\nЦена банка уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_jar_storage_level = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `Уровень банка {upgrade_level}` за 🦚 {upgrade_level_price}.\nВместимость банка теперь 🦚 {upgrade_level * 400}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - upgrade1
        elif upgrade == "upgrade1":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, upgrade1 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 200 + (upgrade_level + 1) * 30

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET upgrade1 = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `{loc.upg1} {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - upgrade2
        elif upgrade == "upgrade2":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, upgrade2 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 400 + (upgrade_level + 1) * 60

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET upgrade2 = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `{loc.upg2} {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - upgrade3
        elif upgrade == "upgrade3":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, upgrade3 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 800 + (upgrade_level + 1) * 90

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET upgrade3 = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `{loc.upg3} {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - upgrade4
        elif upgrade == "upgrade4":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, upgrade4 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 1600 + (upgrade_level + 1) * 120

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET upgrade4 = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `{loc.upg4} {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - upgrade5
        elif upgrade == "upgrade5":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, upgrade5 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 3200 + (upgrade_level + 1) * 150

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET upgrade5 = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `{loc.upg5} {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - upgrade6
        elif upgrade == "upgrade6":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, upgrade6 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 6400 + (upgrade_level + 1) * 180

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET upgrade6 = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `{loc.upg6} {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - upgrade7
        elif upgrade == "upgrade7":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_counter, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            author_cookies = data[0]
            upgrade_level = data[1]

            # Calculate price
            upgrade_level_price = 12800 + (upgrade_level + 1) * 210

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            # Enough funds
            else:
                # Update database
                upgrade_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET upgrade7 = {upgrade_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

                # Close
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                            description=f"<@{ctx.user.id}> успешно приобретает `{loc.upg7} {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

        # Upgrade - Help
        elif upgrade == "help":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            sql_connection.close()

            # Calculate prices
            price_bank = f"🦚 {200 * 2 ** (data[0] + 1)}"
            price_upg1 = f"🦚 {200 + (data[1] + 1) * 30}"
            price_upg2 = f"🦚 {400 + (data[2] + 1) * 60}"
            price_upg3 = f"🦚 {800 + (data[3] + 1) * 90}"
            price_upg4 = f"🦚 {1600 + (data[4] + 1) * 120}"
            price_upg5 = f"🦚 {3200 + (data[5] + 1) * 150}"
            price_upg6 = f"🦚 {6400 + (data[6] + 1) * 180}"
            price_upg7 = f"🦚 {12800 + (data[7] + 1) * 210}"

            # Reply embed
            reply_embed = discord.Embed(title=f"Стоимость покупки улучшений для {ctx.user}",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            reply_embed.add_field(name=f"Цена банка `{data[0] + 1}` уровня:", value=price_bank, inline=False)
            reply_embed.add_field(name=f"Цена `{loc.upg1}` `{data[1] + 1}` уровня:", value=price_upg1, inline=False)
            reply_embed.add_field(name=f"Цена `{loc.upg2}` `{data[2] + 1}` уровня:", value=price_upg2, inline=False)
            reply_embed.add_field(name=f"Цена `{loc.upg3}` `{data[3] + 1}` уровня:", value=price_upg3, inline=False)
            reply_embed.add_field(name=f"Цена `{loc.upg4}` `{data[4] + 1}` уровня:", value=price_upg4, inline=False)
            reply_embed.add_field(name=f"Цена `{loc.upg5}` `{data[5] + 1}` уровня:", value=price_upg5, inline=False)
            reply_embed.add_field(name=f"Цена `{loc.upg6}` `{data[6] + 1}` уровня:", value=price_upg6, inline=False)
            reply_embed.add_field(name=f"Цена `{loc.upg7}` `{data[7] + 1}` уровня:", value=price_upg7, inline=False)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Error?
        else:
            return await ctx.response.send_message("Error", ephemeral=True)

    @app_commands.command(name="sell_upgrade",
                          description="Продать одно улучшение за 🦚. Цена продажи - 80% от цены покупки.")
    @app_commands.describe(upgrade="Улучшение, которые вы продадите за 🦚")
    @app_commands.choices(upgrade=[
        Choice(name=f'Список стоимости продажи улучшений', value="help"),
        Choice(name=f'Улучшение 1 - {loc.upg1}', value="upgrade1"),
        Choice(name=f'Улучшение 2 - {loc.upg2}', value="upgrade2"),
        Choice(name=f'Улучшение 3 - {loc.upg3}', value="upgrade3"),
        Choice(name=f'Улучшение 4 - {loc.upg4}', value="upgrade4"),
        Choice(name=f'Улучшение 5 - {loc.upg5}', value="upgrade5"),
        Choice(name=f'Улучшение 6 - {loc.upg6}', value="upgrade6"),
        Choice(name=f'Улучшение 7 - {loc.upg7}', value="upgrade7"),
    ])
    async def sell_upgrade(self, ctx: discord.Interaction, upgrade: str):
        # Database connection and default value
        sql_connection = sl.connect("Peacock.db")

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Upgrade - upgrade1
        if upgrade == "upgrade1":
            sql_query = f"SELECT upgrade1 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}"
            data = sql_connection.execute(sql_query).fetchone()
            upgrade_level = data[0]
            upgrade_name = f"`{loc.upg1}`"

        # Upgrade - upgrade2
        elif upgrade == "upgrade2":
            sql_query = f"SELECT upgrade2 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}"
            data = sql_connection.execute(sql_query).fetchone()
            upgrade_level = data[0]
            upgrade_name = f"`{loc.upg2}`"

        # Upgrade - upgrade3
        elif upgrade == "upgrade3":
            sql_query = f"SELECT upgrade3 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}"
            data = sql_connection.execute(sql_query).fetchone()
            upgrade_level = data[0]
            upgrade_name = f"`{loc.upg3}`"

        # Upgrade - upgrade4
        elif upgrade == "upgrade4":
            sql_query = f"SELECT upgrade4 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}"
            data = sql_connection.execute(sql_query).fetchone()
            upgrade_level = data[0]
            upgrade_name = f"`{loc.upg4}`"

        # Upgrade - upgrade5
        elif upgrade == "upgrade5":
            sql_query = f"SELECT upgrade5 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}"
            data = sql_connection.execute(sql_query).fetchone()
            upgrade_level = data[0]
            upgrade_name = f"`{loc.upg5}`"

        # Upgrade - upgrade6
        elif upgrade == "upgrade6":
            sql_query = f"SELECT upgrade6 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}"
            data = sql_connection.execute(sql_query).fetchone()
            upgrade_level = data[0]
            upgrade_name = f"`{loc.upg6}`"

        # Upgrade - upgrade7
        elif upgrade == "upgrade7":
            sql_query = f"SELECT upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}"
            data = sql_connection.execute(sql_query).fetchone()
            upgrade_level = data[0]
            upgrade_name = f"`{loc.upg7}`"

        # Upgrade - Help
        elif upgrade == "help":
            # Info retrieval
            data = sql_connection.execute(
                f"SELECT upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            sql_connection.close()
            # Calculate prices
            price_upg1 = f"🦚 {0.8 * (200 + data[0] * 30)}"
            price_upg2 = f"🦚 {0.8 * (400 + data[1] * 60)}"
            price_upg3 = f"🦚 {0.8 * (800 + data[2] * 90)}"
            price_upg4 = f"🦚 {0.8 * (1600 + data[3] * 120)}"
            price_upg5 = f"🦚 {0.8 * (3200 + data[4] * 150)}"
            price_upg6 = f"🦚 {0.8 * (6400 + data[5] * 180)}"
            price_upg7 = f"🦚 {0.8 * (12800 + data[6] * 210)}"

            # Reply embed
            any_fields_shown = False
            reply_embed = discord.Embed(title=f"Стоимость продажи улучшений для {ctx.user}",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            if data[0] != 0:
                reply_embed.add_field(name=f"Цена улучшения 1 - `{loc.upg1}` `{data[0]}` уровня:", value=price_upg1,
                                      inline=False)
                any_fields_shown = True
            if data[1] != 0:
                reply_embed.add_field(name=f"Цена улучшения 2 - `{loc.upg2}` `{data[1]}` уровня:", value=price_upg2,
                                      inline=False)
                any_fields_shown = True
            if data[2] != 0:
                reply_embed.add_field(name=f"Цена улучшения 3 - `{loc.upg3}` `{data[2]}` уровня:", value=price_upg3,
                                      inline=False)
                any_fields_shown = True
            if data[3] != 0:
                reply_embed.add_field(name=f"Цена улучшения 4 - `{loc.upg4}` `{data[3]}` уровня:", value=price_upg4,
                                      inline=False)
                any_fields_shown = True
            if data[4] != 0:
                reply_embed.add_field(name=f"Цена улучшения 5 - `{loc.upg5}` `{data[4]}` уровня:", value=price_upg5,
                                      inline=False)
                any_fields_shown = True
            if data[5] != 0:
                reply_embed.add_field(name=f"Цена улучшения 6 - {loc.upg6}` `{data[5]}` уровня:", value=price_upg6,
                                      inline=False)
                any_fields_shown = True
            if data[6] != 0:
                reply_embed.add_field(name=f"Цена улучшения 7 - `{loc.upg7}` `{data[6]}` уровня:", value=price_upg7,
                                      inline=False)
                any_fields_shown = True
            if not any_fields_shown:
                reply_embed = discord.Embed(title=f"Стоимость продажи улучшений для {ctx.user}",
                                            description="Вам нечего продавать.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_thumbnail(url=ctx.user.avatar)
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Error?
        else:
            return await ctx.response.send_message("Error", ephemeral=True)

        # Nothing to sell
        if upgrade_level == 0:
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Нечего продавать",
                                        description=f"<@{ctx.user.id}>, вы не можете продать уровень этого улучшения, так как вы не владеете им.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Calculate price
        sell_price = round((200 * (2 ** (int(upgrade[-1]) - 1)) + upgrade_level * 30 * int(upgrade[-1])) * 0.8)

        # Update database
        sql_connection.execute(
            f"UPDATE ECONOMY SET {upgrade} = {upgrade_level - 1} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, ctx.user.id))
        sql_connection.execute(
            f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {sell_price} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, ctx.user.id))

        # Close
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"✅ Успешная продажа",
                                    description=f"<@{ctx.user.id}> успешно продаёт {upgrade_name} `{upgrade_level}` за 🦚 {sell_price}.",
                                    colour=discord.Colour.green())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)

        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="steal", description="Украсть 🦚 из кошелька другого пользователя.")
    @app_commands.describe(member="Пользователь, у которого вы хотите украсть 🦚.")
    async def steal_peacocks(self, ctx: discord.Interaction, member: discord.Member):
        # Check if target is valid
        if ctx.user.id == member.id:  # Target is yourself
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Вы не можете украсть у самого себя.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        elif member.bot:  # Target is bot
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Вы не можете украсть у бота.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Connection to database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, member.id))

        # Check if there is theft cooldown
        last_attempted_theft_epoch = sql_connection.execute(
            f"SELECT last_theft_attempt FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_attempted_theft_epoch + 10 * 60:  # There is a cooldown
            # Close connection
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Попробуйте позже",
                                        description=f"<@{ctx.user.id}>, вы уже попытались ограбить пользователя ранее. Попробуйте снова <t:{last_attempted_theft_epoch + 10 * 60}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        else:  # There is no cooldown - set a new one
            # Get info from database
            target_cookies = sql_connection.execute(
                f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}").fetchone()[
                0]
            author_cookies = sql_connection.execute(
                f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                0]

            # Get percentages and cookies
            success_chance = randint(0, 100)
            cookies_stolen = int(randint(5, 65) / 100 * target_cookies)
            cookies_lost_on_failure = int(randint(5, 15) / 100 * author_cookies)

            # Nothing to steal
            if cookies_stolen == 0:
                # Close database
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Кошелёк {member.name} пуст",
                                            description=f"<@{member.id}> не имеет 🦚 в кошельке.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

            # Update database - theft cooldown
            sql_connection.execute(
                f"UPDATE ECONOMY SET last_theft_attempt = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()

            # Theft - success
            if success_chance >= 50:
                # Update database
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {cookies_stolen} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {cookies_stolen} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, member.id))
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"🕵️ Успешное ограбление {member.name}",
                                            description=f"<@{ctx.user.id}> украл 🦚 {cookies_stolen} у <@{member.id}>.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

            # Theft - Failure
            elif success_chance in range(20, 50):
                # Close database
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Неудачное ограбление {member.name}",
                                            description=f"<@{ctx.user.id}> испугался и ничего не украл у <@{member.id}>.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

            # Theft - Critical failure
            else:
                # Lose all cookies if less than
                if author_cookies < cookies_lost_on_failure:
                    cookies_lost_on_failure = author_cookies

                # Update database
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {cookies_lost_on_failure} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))
                # Close database
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Катастрофическое ограбление {member.name}",
                                            description=f"Ограбление было предотвращено яростным вельш-корги.\n<@{ctx.user.id}> потерял 🦚 {cookies_lost_on_failure}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="deposit", description="Поместить 🦚 в банк.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите положить в банк.")
    async def save_peacocks_in_bank(self, ctx: discord.Interaction, amount: int):
        # Database connection
        sql_connection = sl.connect("Peacock.db")

        # Information retrieval
        data = sql_connection.execute(
            f"SELECT cookie_jar_storage, cookie_jar_storage_level, cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
        author_bank_cookies = data[0]
        author_bank_level = data[1]
        author_wallet = data[2]

        # Target amount is more than you have in your wallet
        if amount > author_wallet:
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, вы не можете положить 🦚 {amount} в банк - у вас всего 🦚 {author_wallet} в вашем кошельке.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Not enough space in bank
        elif amount > author_bank_level * 400 - author_bank_cookies:
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно места в банке",
                                        description=f"<@{ctx.user.id}>, вы не можете положить 🦚 {amount} в банк - у вас есть место только для 🦚 {author_bank_level * 400 - author_bank_cookies} в вашем банке.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Everything is fine
        else:
            # Deposit
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_jar_storage = cookie_jar_storage + {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"🏦 Успешное пополнение банка",
                                        description=f"<@{ctx.user.id}> положил 🦚 {amount} в банк.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="withdraw", description="Забрать 🦚 из банка.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите забрать из банка.")
    async def withdraw_peacocks_from_bank(self, ctx: discord.Interaction, amount: int):
        # Database connection
        sql_connection = sl.connect("Peacock.db")

        # Information retrieval
        author_bank_cookies = sql_connection.execute(
            f"SELECT cookie_jar_storage FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]

        # More demanded than in bank
        if amount > author_bank_cookies:
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств в банке",
                                        description=f"<@{ctx.user.id}>, вы не можете забрать 🦚 {amount} - у вас всего 🦚 {author_bank_cookies} в банке.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Everything is fine
        else:
            # Database update
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_jar_storage = cookie_jar_storage - {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"🏦 Успешное изъятие средств из банка",
                                        description=f"<@{ctx.user.id}> забрал 🦚 {amount} из банка.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="work", description="Работа и получить 🦚 за приобретённые улучшения. Work in progress.")
    async def work(self, ctx: discord.Interaction):
        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Check if there is message cooldown
        last_daily_bonus_received_epoch = sql_connection.execute(
            f"SELECT last_access FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_daily_bonus_received_epoch + 3600 * 2:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Ошибка",
                                        description=f"Работа ещё не появилась. Вернитесь <t:{last_daily_bonus_received_epoch + 3600}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Calculate income
            gained_from_work = randint(250, 500)
            amount_gained = gained_from_work
            upg1_income = sql_connection.execute(
                f"SELECT upgrade1 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                              0] * 5
            amount_gained += upg1_income
            upg2_income = sql_connection.execute(
                f"SELECT upgrade2 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                              0] * 15
            amount_gained += upg2_income
            upg3_income = sql_connection.execute(
                f"SELECT upgrade3 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                              0] * 35
            amount_gained += upg3_income
            upg4_income = sql_connection.execute(
                f"SELECT upgrade4 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                              0] * 75
            amount_gained += upg4_income
            upg5_income = sql_connection.execute(
                f"SELECT upgrade5 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                              0] * 170
            amount_gained += upg5_income
            upg6_income = sql_connection.execute(
                f"SELECT upgrade6 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                              0] * 370
            amount_gained += upg6_income
            upg7_income = sql_connection.execute(
                f"SELECT upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
                              0] * 495
            amount_gained += upg7_income

            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET last_access = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {amount_gained} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Работа",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            reply_embed.add_field(name=f"Доход от работы:",
                                  value=f"🦚 {gained_from_work}",
                                  inline=False)
            if upg1_income > 0:
                reply_embed.add_field(name=f"Доход от `{loc.upg1}`:",
                                      value=f"🦚 {upg1_income} = 5 x {upg1_income / 5}",
                                      inline=False)
            if upg2_income > 0:
                reply_embed.add_field(name=f"Доход от `{loc.upg2}`:",
                                      value=f"🦚 {upg2_income} = 15 x {upg2_income / 15}",
                                      inline=False)
            if upg3_income > 0:
                reply_embed.add_field(name=f"Доход от `{loc.upg3}`:",
                                      value=f"🦚 {upg3_income} = 35 x {upg3_income / 35}",
                                      inline=False)
            if upg4_income > 0:
                reply_embed.add_field(name=f"Доход от `{loc.upg4}`:",
                                      value=f"🦚 {upg4_income} = 75 x {upg4_income / 75}",
                                      inline=False)
            if upg5_income > 0:
                reply_embed.add_field(name=f"Доход от `{loc.upg5}`:",
                                      value=f"🦚 {upg5_income} = 170 x {upg5_income / 170}",
                                      inline=False)
            if upg6_income > 0:
                reply_embed.add_field(name=f"Доход от `{loc.upg6}`:",
                                      value=f"🦚 {upg6_income} = 370 x {upg6_income / 370}",
                                      inline=False)
            if upg7_income > 0:
                reply_embed.add_field(name=f"Доход от улучшение7:",
                                      value=f"🦚 {upg7_income} = 495 x {upg7_income / 495}",
                                      inline=False)
            reply_embed.add_field(name="Итого:",
                                  value=f"Вы заработали 🦚 {amount_gained}.",
                                  inline=False)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)


class peacockAdminEconomyCog(commands.GroupCog, name="adm_economy"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_peacocks", description="Создать 🦚 для пользователя.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите предоставить пользователю.",
                           target="Пользователь, кто получит 🦚.")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_peacocks(self, ctx: discord.Interaction, target: discord.Member, amount: int):
        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')

        # Database update
        sql_connection.execute(
            f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {amount} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, target.id))

        # Close
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"Создание валюты",
                                    description=f"🦚 {amount} было создано для {target}",
                                    colour=discord.Colour.green())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @create_peacocks.error
    async def on_user_missing_permissions_error(self, interaction: discord.Interaction,
                                                error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message(str(error), ephemeral=True)

    @app_commands.command(name="remove_peacocks_wallet", description="Забрать 🦚 из кошелька пользователя.")
    @app_commands.describe(amount="Количество 🦚, которое вы забрать у пользователя.",
                           target="Пользователь, кто потеряет из своего кошелька 🦚.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_peacocks_wallet(self, ctx: discord.Interaction, target: discord.Member, amount: int):
        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, target.id))

        target_cookies = sql_connection.execute(
            f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {target.id}").fetchone()[
            0]

        # Database update
        if amount < target_cookies:
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, target.id))
        else:
            amount = target_cookies
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = 0 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, target.id))

        # Close
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"Изъятие валюты",
                                    description=f"🦚 {amount} было забрано из кошелька {target}",
                                    colour=discord.Colour.green())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @remove_peacocks_wallet.error
    async def on_user_missing_permissions_error(self, interaction: discord.Interaction,
                                                error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message(str(error), ephemeral=True)

    @app_commands.command(name="remove_peacocks_bank", description="Забрать 🦚 из банка пользователя.")
    @app_commands.describe(amount="Количество 🦚, которое вы забрать у пользователя.",
                           target="Пользователь, кто потеряет из своего банка 🦚.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_peacocks_bank(self, ctx: discord.Interaction, target: discord.Member, amount: int):
        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, target.id))

        target_cookies = sql_connection.execute(
            f"SELECT cookie_jar_storage FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {target.id}").fetchone()[
            0]

        # Database update
        if amount < target_cookies:
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_jar_storage = cookie_jar_storage - {amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, target.id))
        else:
            amount = target_cookies
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_jar_storage = 0 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, target.id))

        # Close
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"Изъятие валюты из банка",
                                    description=f"🦚 {amount} было забрано из банка {target}",
                                    colour=discord.Colour.green())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @remove_peacocks_bank.error
    async def on_user_missing_permissions_error(self, interaction: discord.Interaction,
                                                error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message(str(error), ephemeral=True)


class peacockEconomyShop(commands.GroupCog, name="shop"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_role", description="Купить роль за 🦚.")
    @app_commands.describe(role="Улучшение, которые вы купите за 🦚")
    @app_commands.choices(role=[
        Choice(name='Абонемент в архив грехов', value="role0"),
        Choice(name=f'Писарь грехов', value="role1"),
        Choice(name=f'Османский', value="role2"),
        Choice(name=f'Прусский', value="role3"),
        Choice(name=f'Нидерландский', value="role4"),
        Choice(name=f'Гордость', value="role5"),
        Choice(name=f'Who?', value="role6"),
    ])
    async def buy_role(self, ctx: discord.Interaction, role: str):
        # Database connection
        sql_connection = sl.connect("Peacock.db")

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Info retrieval
        author_cookies = sql_connection.execute(
            f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]
        choice_role_dict = {
            "role0": loc.archive_role,
            "role1": loc.sin_writer_role,
            "role2": loc.ottoman_role,
            "role3": loc.prussian_role,
            "role4": loc.dutch_role,
            "role5": loc.pride_role,
            "role6": loc.dzen_role,
        }
        # Role ID
        role_id = choice_role_dict[role]
        # Price of role
        price = loc.shop_role_pricelist[role_id]
        # Role object
        role = discord.Object(role_id)
        # Role flag
        already_has_this_role = False
        for member_role in ctx.user.roles:
            if member_role.id == role_id:
                already_has_this_role = True

        # Check if member already has this role
        if already_has_this_role:
            # Close
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Ошибка",
                                        description=f"<@{ctx.user.id}>, у вас уже есть эта роль.",
                                        colour=discord.Colour.dark_gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        # Check if enough funds
        elif author_cookies < price:  # Not enough funds
            # Close
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, вы не можете купить данную роль.\nВаш кошелёк: 🦚 `{author_cookies}`\nЦена роли: 🦚 `{price}`.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {price} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))

            # Close
            sql_connection.commit()
            sql_connection.close()

            # Give role
            await ctx.user.add_roles(role, reason="Купил роль за 🦚")

            # Reply embed
            reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                        description=f"<@{ctx.user.id}> успешно приобретает новую роль за 🦚 {price}.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

    @app_commands.command(name="timeout", description=" за 🦚.")
    @app_commands.describe(timeout_duration="Улучшение, которые вы купите за 🦚")
    @app_commands.choices(timeout_duration=[
        Choice(name='Убрать мут с участника', value=0),
        Choice(name='1 минута', value=1),
        Choice(name=f'10 минут', value=10),
        Choice(name=f'30 минут', value=30),
        Choice(name=f'1 час', value=60),
        Choice(name=f'24 часа', value=60 * 24),
    ])
    async def buy_upgrade(self, ctx: discord.Interaction, target: discord.Member, timeout_duration: int):
        # Database connection
        sql_connection = sl.connect("Peacock.db")

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Info retrieval
        author_cookies = sql_connection.execute(
            f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()[
            0]
        price = 2000 * timeout_duration if timeout_duration != 0 else 10000

        # Check if target is muted and someone wants to mute them again
        if target.is_timed_out() and timeout_duration != 0:
            # Close
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Ошибка",
                                        description=f"<@{target.id}> уже имеет мут.",
                                        colour=discord.Colour.dark_gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        elif not target.is_timed_out() and timeout_duration == 0:
            # Close
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Ошибка",
                                        description=f"<@{target.id}> не имеет мут.",
                                        colour=discord.Colour.dark_gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        # Check if enough funds
        elif author_cookies < price:  # Not enough funds
            # Close
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, вы не можете купить данную услугу.\nВаш кошелёк: 🦚 `{author_cookies}`\nЦена услуги: 🦚 `{price}`.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {price} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))

            # Close
            sql_connection.commit()
            sql_connection.close()

            # Timeout
            timeout = datetime.datetime.now().astimezone() + datetime.timedelta(minutes=timeout_duration)
            await target.edit(timed_out_until=timeout)

            # Reply embed
            reply_embed = discord.Embed(title=f"✅ Успешная покупка мута для {target}",
                                        description=f"<@{ctx.user.id}> успешно приобретает мут для <@{target.id}> на `{timeout_duration}` минут за 🦚 {price}.",
                                        colour=discord.Colour.green()) if timeout_duration != 0 else discord.Embed(
                title=f"✅ Успешная покупка снятия мута для {target}",
                description=f"<@{ctx.user.id}> успешно приобретает снятие мута для <@{target.id}> за 🦚 {price}.",
                colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)


async def setup(bot):
    sql_connection = sl.connect('Peacock.db')
    sql_connection.execute(
        f"CREATE TABLE IF NOT EXISTS ECONOMY (guild_id int, user_id int, cookie_counter int, cookie_jar_storage int, cookie_jar_storage_level int, upgrade1 int, upgrade2 int, upgrade3 int, upgrade4 int, upgrade5 int, upgrade6 int, upgrade7 int, last_access int, daily_bonus int, weekly_bonus int, monthly_bonus int, message_cooldown int, last_theft_attempt int, primary key (guild_id, user_id))")
    sql_connection.commit()
    sql_connection.close()
    await bot.add_cog(peacockEconomyCog(bot))
    await bot.add_cog(peacockAdminEconomyCog(bot))
    await bot.add_cog(peacockEconomyShop(bot))
