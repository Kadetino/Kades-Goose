import discord  # Discord API wrapper
from discord import app_commands  # Slash commands
from discord.app_commands import Choice  # Slash command choices
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
from random import randint  # Random number generation for economy
from config import prefix, cd_commands  # Global settings
from time import time  # Epoch timestamp
import datetime  # Timestamps in embeds


class peacockEconomyCog(commands.GroupCog, name="economy"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def on_message_give_peacocks(self, user_message: discord.message.Message):
        """Gain peacocks per sent message. Cooldown 10 seconds. Bonus points for using peacock emote."""
        # print("Message: ", user_message)
        # print("Content: ", str(user_message.content))
        # print("Guild id: ", str(user_message.guild.id))
        # print("Author id: ", str(user_message.author.id))

        # Checks and connecting database
        if user_message.author.bot or user_message.content.startswith(prefix):
            return
        sql_connection = sl.connect('Goose.db')

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
        sql_connection = sl.connect("Goose.db")

        # Profile retrieval
        data = sql_connection.execute(
            f"SELECT cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}").fetchone()
        sql_connection.close()

        # Nothing found
        if data is None:
            return await ctx.response.send_message(f"<@{member.id}> не имеет профиля.", ephemeral=True)
        else:
            member_cookies = f"🦚 {data[0]}"
            bank_info = f"🦚 {data[1]} из {data[2] * 400}"
            upgrade_info = f"улучшение1: {data[3]}\n" \
                           f"улучшение2: {data[4]}\n" \
                           f"улучшение3: {data[5]}\n" \
                           f"улучшение4: {data[6]}\n" \
                           f"улучшение5: {data[7]}\n" \
                           f"улучшение6: {data[8]}\n" \
                           f"улучшение7: {data[9]}"
            total_info = data[0] + data[1]
            price = 500
            for i in range(3, 10):
                total_info += round(data[i] * price * 0.8)
                price = price * 2 + 100
            total_info = f"🦚 {total_info}"

        # Reply embed
        reply_embed = discord.Embed(title=f"Профиль {member.name}",
                                    colour=discord.Colour.gold())
        reply_embed.timestamp = datetime.datetime.utcnow()
        reply_embed.set_thumbnail(url=member.avatar)
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        reply_embed.add_field(name=f"Кошелёк:", value=member_cookies, inline=False)
        reply_embed.add_field(name=f"Банк:", value=bank_info, inline=False)
        reply_embed.add_field(name=f"Улучшения:", value=upgrade_info, inline=False)
        reply_embed.add_field(name=f"`Итого:`", value=total_info, inline=False)

        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="daily", description="Получить ежедневный бонус.")
    async def daily_bonus(self, ctx: discord.Interaction):
        # Сonnecting database
        sql_connection = sl.connect('Goose.db')

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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

    @app_commands.command(name="weekly", description="Получить еженедельный бонус.")
    async def weekly_bonus(self, ctx: discord.Interaction):
        # Connecting database
        sql_connection = sl.connect('Goose.db')

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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

    @app_commands.command(name="monthly", description="Получить ежемесячный бонус.")
    async def monthly_bonus(self, ctx: discord.Interaction):
        # Connecting database
        sql_connection = sl.connect('Goose.db')

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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed = discord.Embed(title=f"💰 Бонус месяца>",
                                        description=f"Вы получили еженедельную награду в 🦚 1500.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="Просмотреть таблицу лидеров.")
    async def economyboard(self, ctx: discord.Interaction):
        # TODO
        # Init
        sql_connection = sl.connect('Goose.db')
        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.user.id))

        # Get data and close
        data = sql_connection.execute(
            f"select user_id, cookie_counter, cookie_jar_storage from ECONOMY where guild_id = {ctx.guild.id}").fetchall()
        sql_connection.commit()
        sql_connection.close()

        # Check if data is empty
        if len(data) == 0:
            return await ctx.response.send_message("Nothing to show.", ephemeral=True)

        # Calculate total amount of peacocks
        storage = []
        author_entry = "Error"
        for line in data:
            total_peacocks = line[1] + line[2]
            # Get user by his id
            user = self.bot.get_user(line[0])
            # If getting user failed
            if user is None:
                continue
            # Adding value to storage
            storage.append((f"{user}", total_peacocks))
            # # Save variable if it was the author
            # if ctx.author.id == line[0]:
            #     author_entry = f"You: `#{len(storage)}` {user}: 🦚 {total_peacocks}"

        # Sort storage for leaderboard
        storage.sort(key=lambda y: y[1], reverse=True)

        # Author stats
        for i in range(len(storage)):
            if storage[i][0] == str(ctx.user):
                author_entry = f"Your position: `#{i + 1}` {ctx.user}: 🦚 {storage[i][1]}"
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
                                value=f"🦚 {storage[i][1]} peacocks",
                                inline=False)
            elif i == 1:
                embed.add_field(name=f":second_place: {storage[i][0]}",
                                value=f"🦚 {storage[i][1]} peacocks",
                                inline=False)
            elif i == 2:
                embed.add_field(name=f":third_place: {storage[i][0]}",
                                value=f"🦚 {storage[i][1]} peacocks",
                                inline=False)
            else:
                embed.add_field(name=f"`#{i + 1}` {storage[i][0]}",
                                value=f"🦚 {storage[i][1]} peacocks",
                                inline=False)

        # Embed: Icon and description on how it works
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.add_field(name=f"❓ How it works?",
                        value=f"You get 🦚 for your messages, `{prefix}daily`, `{prefix}weekly` or `{prefix}monthly`. Bonus points if you user 🦚 emoji in your messages!",
                        inline=False)
        embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        elif ctx.user.id == member.id:  # Target is yourself
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Вы не можете перевести самому себе.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Connection to database and retrieving authors peacocks
        sql_connection = sl.connect('Goose.db')
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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
        Choice(name='Список стоимости улучшений', value="help"),
        Choice(name='Банк', value="bank"),
        Choice(name='Улучшение1', value="upgrade1"),
        Choice(name='Улучшение2', value="upgrade2"),
        Choice(name='Улучшение3', value="upgrade3"),
        Choice(name='Улучшение4', value="upgrade4"),
        Choice(name='Улучшение5', value="upgrade5"),
        Choice(name='Улучшение6', value="upgrade6"),
        Choice(name='Улучшение7', value="upgrade7"),
    ])
    async def buy_upgrade(self, ctx: discord.Interaction, upgrade: str):
        # Database connection
        sql_connection = sl.connect("Goose.db")

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
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Уровень банка {upgrade_level}` за 🦚 {upgrade_level_price}.\nВместимость банка <@{ctx.user.id}> теперь 🦚 {upgrade_level * 400}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            upgrade_level_price = 200 + upgrade_level * 30

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Улучшение1 {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            upgrade_level_price = 400 + upgrade_level * 60

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Улучшение2 {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            upgrade_level_price = 800 + upgrade_level * 90

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Улучшение3 {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            upgrade_level_price = 1600 + upgrade_level * 120

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Улучшение4 {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            upgrade_level_price = 3200 + upgrade_level * 150

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Улучшение5 {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            upgrade_level_price = 6400 + upgrade_level * 180

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Улучшение6 {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            upgrade_level_price = 12800 + upgrade_level * 210

            # Check if enough funds
            if author_cookies < upgrade_level_price:  # Not enough funds
                # Close
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                            description=f"<@{ctx.user.id}>, вы не можете купить следующий уровень этого улучшения.\nВаш кошелёк: 🦚 {author_cookies}\nЦена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"<@{ctx.user.id}> успешно приобретает `Улучшение7 {upgrade_level}` за 🦚 {upgrade_level_price}.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = datetime.datetime.utcnow()
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
            price_bank = f"🦚 {200 * 2 ** (data[0]+1)}"
            price_upg1 = f"🦚 {200 + (data[1]+1) * 30}"
            price_upg2 = f"🦚 {400 + (data[2]+1) * 60}"
            price_upg3 = f"🦚 {800 + (data[3]+1) * 90}"
            price_upg4 = f"🦚 {1600 + (data[4]+1) * 120}"
            price_upg5 = f"🦚 {3200 + (data[5]+1) * 150}"
            price_upg6 = f"🦚 {6400 + (data[6]+1) * 180}"
            price_upg7 = f"🦚 {12800 + (data[7]+1) * 210}"

            # Reply embed
            reply_embed = discord.Embed(title=f"Стоимость улучшений для {ctx.user}",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            reply_embed.add_field(name=f"Цена банка `{data[0]+1}` уровня:", value=price_bank, inline=False)
            reply_embed.add_field(name=f"Цена улучшение1 `{data[1]+1}` уровня:", value=price_upg1, inline=False)
            reply_embed.add_field(name=f"Цена улучшение2 `{data[2]+1}` уровня:", value=price_upg2, inline=False)
            reply_embed.add_field(name=f"Цена улучшение3 `{data[3]+1}` уровня:", value=price_upg3, inline=False)
            reply_embed.add_field(name=f"Цена улучшение4 `{data[4]+1}` уровня:", value=price_upg4, inline=False)
            reply_embed.add_field(name=f"Цена улучшение5 `{data[5]+1}` уровня:", value=price_upg5, inline=False)
            reply_embed.add_field(name=f"Цена улучшение6 `{data[6]+1}` уровня:", value=price_upg6, inline=False)
            reply_embed.add_field(name=f"Цена улучшение7 `{data[7]+1}` уровня:", value=price_upg7, inline=False)


            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Error?
        else:
            return await ctx.response.send_message("Error", ephemeral=True)

    @commands.command(name="sell_upgrade", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def sell_upgrade(self, ctx: commands.Context, target_upgrade: str, target_quantity: int):
        # TODO
        return

    @app_commands.command(name="steal", description="Украсть 🦚 из кошелька другого пользователя.")
    @app_commands.describe(member="Пользователь, у которого вы хотите украсть 🦚.")
    async def steal_peacocks(self, ctx: discord.Interaction, member: discord.Member):
        # Check if target is valid
        if ctx.user.id == member.id:  # Target is yourself
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Вы не можете украсть у самого себя.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        elif member.bot:  # Target is bot
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Вы не можете украсть у бота.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Connection to database
        sql_connection = sl.connect('Goose.db')

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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                reply_embed.timestamp = datetime.datetime.utcnow()
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
                                            description=f"Ограбление <@{ctx.user.id}> было предотвращено яростным вельш-корги.\n<@{ctx.user.id}> потерял 🦚 {cookies_lost_on_failure}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = datetime.datetime.utcnow()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="deposit", description="Поместить 🦚 в банк.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите положить в банк.")
    async def save_peacocks_in_bank(self, ctx: discord.Interaction, amount: int):
        # Database connection
        sql_connection = sl.connect("Goose.db")

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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed = discord.Embed(title=f"✅ Успешное пополнение банка",
                                        description=f"<@{ctx.user.id}> положил 🦚 {amount} в банк.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="withdraw", description="Забрать 🦚 из банка.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите забрать из банка.")
    async def withdraw_peacocks_from_bank(self, ctx: discord.Interaction, amount: int):
        # Database connection
        sql_connection = sl.connect("Goose.db")

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
            reply_embed.timestamp = datetime.datetime.utcnow()
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
            reply_embed = discord.Embed(title=f"✅ Успешное изъятие средств из банка",
                                        description=f"<@{ctx.user.id}> забрал 🦚 {amount} из банка.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @commands.command(name="work", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def work(self, ctx: commands.Context):
        # TODO and maybe increase command cooldown. and include upgrade calculation here
        return


async def setup(bot):
    sql_connection = sl.connect('Goose.db')
    sql_connection.execute(
        f"CREATE TABLE IF NOT EXISTS ECONOMY (guild_id int, user_id int, cookie_counter int, cookie_jar_storage int, cookie_jar_storage_level int, upgrade1 int, upgrade2 int, upgrade3 int, upgrade4 int, upgrade5 int, upgrade6 int, upgrade7 int, last_access int, daily_bonus int, weekly_bonus int, monthly_bonus int, message_cooldown int, last_theft_attempt int, primary key (guild_id, user_id))")
    sql_connection.close()
    await bot.add_cog(peacockEconomyCog(bot))
