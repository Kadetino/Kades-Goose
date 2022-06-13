import discord  # Discord API wrapper
from discord import app_commands  # Slash commands
from discord.app_commands import Choice  # Slash command choices
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
from random import randint  # Random number generation for economy
from config import prefix  # Global settings
from time import time  # Epoch timestamp
import datetime  # Shop - timeout

import cog_settings.peacock_economy_settings as loc
import cog_settings.peacock_economy_db_queries as dbq


class peacockEconomyCog(commands.GroupCog, name="economy"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def on_message_give_peacocks(self, user_message: discord.message.Message):
        # TODO rework and dms

        # Checks and connecting database
        if user_message.author.bot or user_message.content.startswith(prefix):
            return
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, user_message.guild.id, user_message.author.id)

        # Check if there is message cooldown
        database_entry = dbq.get_user_column_info(sql_connection, user_message.guild.id, user_message.author.id,
                                                  "message_cooldown")
        epoch_right_now = int(time())
        if epoch_right_now < database_entry + loc.peacock_gain_per_message_cooldown:
            return sql_connection.close()
        else:
            sql_connection.execute(
                f"UPDATE ECONOMY SET message_cooldown = {epoch_right_now} WHERE guild_id = ? AND user_id = ?",
                (user_message.guild.id, user_message.author.id))
            sql_connection.commit()

        # Amount of peacocks gained per message: bonus points for using specific emoji
        peacocks_gained = loc.peacocks_gained_per_message()
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
        # TODO display different profiles
        # TODO Rework
        # Check if user argument was provided
        if member is None:
            member = ctx.user

        # Database connection
        sql_connection = sl.connect('Peacock.db')

        # Profile retrieval
        data = sql_connection.execute(
            f"SELECT cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}").fetchone()
        cooldown_data = sql_connection.execute(
            f"SELECT last_access, last_theft_attempt, daily_bonus, weekly_bonus, monthly_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}").fetchone()
        # infamy_lvl = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "infamy_lvl")
        fame_lvl = dbq.get_user_column_info(sql_connection, ctx.guild.id, member.id, "fame_lvl")
        lockpicks = dbq.get_user_column_info(sql_connection, ctx.guild.id, member.id, "lockpicks")
        sql_connection.close()

        # Nothing found
        if data is None:
            return await ctx.response.send_message(f"<@{member.id}> не имеет профиля.", ephemeral=True)
        else:
            member_cookies = f"🦚 {data[0]}"
            bank_info = f"🦚 {data[1]} из {data[2] * dbq.bank_capacity_per_lvl(ctx)}"
            upgrade_info = f"`{loc.upgrade_name_dict['upgrade1']}`: {data[3]} уровень\n" \
                           f"`{loc.upgrade_name_dict['upgrade2']}`: {data[4]} уровень\n" \
                           f"`{loc.upgrade_name_dict['upgrade3']}`: {data[5]} уровень\n" \
                           f"`{loc.upgrade_name_dict['upgrade4']}`: {data[6]} уровень\n" \
                           f"`{loc.upgrade_name_dict['upgrade5']}`: {data[7]} уровень\n" \
                           f"`{loc.upgrade_name_dict['upgrade6']}`: {data[8]} уровень\n" \
                           f"`{loc.upgrade_name_dict['upgrade7']}`: {data[9]} уровень\n"
            total_info = f"~ 🦚 {data[0] + data[1]}"
            cooldown_info = ""
            # Work timer
            if cooldown_data[0] + loc.work_bonus_cooldown < int(time()):
                cooldown_info += ", `/work`"
            # Daily bonus timer
            if cooldown_data[2] + loc.daily_bonus_cooldown < int(time()):
                cooldown_info += ", `/daily`"
            # Weekly bonus timer
            if cooldown_data[3] + loc.weekly_bonus_cooldown < int(time()):
                cooldown_info += ", `/weekly`"
            # Monthly bonus timer
            if cooldown_data[4] + loc.monthly_bonus_cooldown < int(time()):
                cooldown_info += ", `/monthly`"
            # Theft timer
            if cooldown_data[1] + loc.theft_cooldown < int(time()):
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
        reply_embed.add_field(name=f"Прочее:", value=f'Отмычки: {lockpicks} штук\n'
                                                     f'Уровень Бизнесмен: {fame_lvl}', inline=False)
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
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Check if there is message cooldown
        last_cd_epoch = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "daily_bonus")
        epoch_right_now = int(time())
        if epoch_right_now < last_cd_epoch + loc.daily_bonus_cooldown:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Бонус дня",
                                        description=f"Вы уже получили свой ежедневный бонус. "
                                                    f"Вернитесь <t:{last_cd_epoch + loc.daily_bonus_cooldown}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update database
            dbq.claim_peacock_bonus(sql_connection, ctx.guild.id, ctx.user.id, "daily_bonus", loc.daily_bonus_,
                                    epoch_right_now)
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Бонус дня",
                                        description=f"Вы получили ежедневную награду в 🦚 {loc.daily_bonus_}.",
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
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Check if there is message cooldown
        last_cd_epoch = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "weekly_bonus")
        epoch_right_now = int(time())
        if epoch_right_now < last_cd_epoch + loc.weekly_bonus_cooldown:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Бонус недели",
                                        description=f"Вы уже получили свой еженедельный бонус. "
                                                    f"Вернитесь <t:{last_cd_epoch + loc.weekly_bonus_cooldown}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update database
            dbq.claim_peacock_bonus(sql_connection, ctx.guild.id, ctx.user.id, "weekly_bonus", loc.weekly_bonus_,
                                    epoch_right_now)
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Бонус недели",
                                        description=f"Вы получили еженедельную награду в 🦚 {loc.weekly_bonus_}.",
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
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Check if there is message cooldown
        last_cd_epoch = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "monthly_bonus")
        epoch_right_now = int(time())
        if epoch_right_now < last_cd_epoch + loc.monthly_bonus_cooldown:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Бонус месяца",
                                        description=f"Вы уже получили свой ежемесячный бонус. "
                                                    f"Вернитесь <t:{last_cd_epoch + loc.monthly_bonus_cooldown}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Update database
            dbq.claim_peacock_bonus(sql_connection, ctx.guild.id, ctx.user.id, "monthly_bonus", loc.monthly_bonus_,
                                    epoch_right_now)
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Бонус месяца",
                                        description=f"Вы получили ежемесячную награду в 🦚 {loc.monthly_bonus_}.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="leaderboard", description="Просмотреть таблицу лидеров. Work in progress.")
    async def economyboard(self, ctx: discord.Interaction):
        # TODO Rework
        # Connect to database
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

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
                                value=f"Всего: 🦚 {storage[i][1]}\n"
                                      f"Кошелёк: 🦚 {storage[i][2]}\n"
                                      f"Банк: 🦚 {storage[i][3]}",
                                inline=False)
            elif i == 1:
                embed.add_field(name=f":second_place: {storage[i][0]}",
                                value=f"Всего: 🦚 {storage[i][1]}\n"
                                      f"Кошелёк: 🦚 {storage[i][2]}\n"
                                      f"Банк: 🦚 {storage[i][3]}",
                                inline=False)
            elif i == 2:
                embed.add_field(name=f":third_place: {storage[i][0]}",
                                value=f"Всего: 🦚 {storage[i][1]}\n"
                                      f"Кошелёк: 🦚 {storage[i][2]}\n"
                                      f"Банк: 🦚 {storage[i][3]}",
                                inline=False)
            else:
                embed.add_field(name=f"`#{i + 1}` {storage[i][0]}",
                                value=f"Всего: 🦚 {storage[i][1]}\n"
                                      f"Кошелёк: 🦚 {storage[i][2]}\n"
                                      f"Банк: 🦚 {storage[i][3]}",
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
        # TODO Rework?
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
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)
        author_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_counter")

        # Check if author has sufficien amount of peacocks
        if author_cookies < round(amount * 1.05) + 1:  # He doesn't have enough
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, у вас недостаточно 🦚 "
                                                    f"для перевода другому человеку.\n"
                                                    f"Вы имеете 🦚 {author_cookies} в кошельке.\n"
                                                    f"Вам необходимо иметь сумму перевода "
                                                    f"и заплатить 5% от неё как комиссию.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            # Close connection and reply
            sql_connection.close()

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:  # Author has enough
            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Успешный перевод",
                                        description=f"<@{member.id}> получил 🦚 {amount} от <@{ctx.user.id}>.\n\n"
                                                    f"Комиссия была 5% 🦚.",
                                        colour=discord.Colour.green())
            reply_embed.set_thumbnail(url=member.avatar)
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, member.id)

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
        Choice(name='Банк', value="cookie_jar_storage_level"),
        Choice(name=f'Улучшение 1 - {loc.upgrade_name_dict["upgrade1"]}', value="upgrade1"),
        Choice(name=f'Улучшение 2 - {loc.upgrade_name_dict["upgrade2"]}', value="upgrade2"),
        Choice(name=f'Улучшение 3 - {loc.upgrade_name_dict["upgrade3"]}', value="upgrade3"),
        Choice(name=f'Улучшение 4 - {loc.upgrade_name_dict["upgrade4"]}', value="upgrade4"),
        Choice(name=f'Улучшение 5 - {loc.upgrade_name_dict["upgrade5"]}', value="upgrade5"),
        Choice(name=f'Улучшение 6 - {loc.upgrade_name_dict["upgrade6"]}', value="upgrade6"),
        Choice(name=f'Улучшение 7 - {loc.upgrade_name_dict["upgrade7"]}', value="upgrade7"),
    ])
    async def buy_upgrade(self, ctx: discord.Interaction, upgrade: str):
        # Database connection
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Upgrade - Help
        if upgrade == "help":
            # Info retrieval
            upg_lvl_data = sql_connection.execute(
                f"SELECT cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"Стоимость покупки улучшений для {ctx.user}",
                                        colour=discord.Colour.yellow())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            reply_embed.add_field(name=f"Цена банка `{upg_lvl_data[0] + 1}` уровня:",
                                  value=f"🦚 {loc.upgrade_prices_functions_dict['cookie_jar_storage_level']((upg_lvl_data[0] + 1))}",
                                  inline=False)
            for i in range(1, len(upg_lvl_data)):
                if 1 == 1:
                    upgrade = f'upgrade{i}'
                    reply_embed.add_field(
                        name=f"Цена улучшения {i} - `{loc.upgrade_name_dict[upgrade]}` `{upg_lvl_data[i] + 1}` уровня:",
                        value=f"🦚 {loc.upgrade_prices_functions_dict[upgrade](upg_lvl_data[i] + 1)}",
                        inline=False)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Info retrieval
        author_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_counter")
        upgrade_level = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, upgrade)
        upgrade_name = loc.upgrade_name_dict[upgrade]

        # Calculate price
        upgrade_level_price = loc.upgrade_prices_functions_dict[upgrade](upgrade_level + 1)

        # Check if enough funds
        if author_cookies < upgrade_level_price:  # Not enough funds
            # Close
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, вы не можете купить следующий "
                                                    f"уровень этого улучшения.\n"
                                                    f"Ваш кошелёк: 🦚 {author_cookies}\n"
                                                    f"Цена этого улучшения уровня `{upgrade_level + 1}`: 🦚 {upgrade_level_price}.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Enough funds
        else:
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET {upgrade} = {upgrade_level + 1} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {upgrade_level_price} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))

            # Close
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"✅ Успешная покупка",
                                        description=f"<@{ctx.user.id}> успешно приобретает `{upgrade_name} "
                                                    f"{upgrade_level + 1}` за 🦚 {upgrade_level_price}.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="sell_upgrade",
                          description="Продать одно улучшение за 🦚. Цена продажи - 80% от цены покупки.")
    @app_commands.describe(upgrade="Улучшение, которые вы продадите за 🦚",
                           quantity="Количество продаваемых улучшений")
    @app_commands.choices(upgrade=[
        Choice(name=f'Список стоимости продажи улучшений', value="help"),
        Choice(name=f'Улучшение 1 - {loc.upgrade_name_dict["upgrade1"]}', value="upgrade1"),
        Choice(name=f'Улучшение 2 - {loc.upgrade_name_dict["upgrade2"]}', value="upgrade2"),
        Choice(name=f'Улучшение 3 - {loc.upgrade_name_dict["upgrade3"]}', value="upgrade3"),
        Choice(name=f'Улучшение 4 - {loc.upgrade_name_dict["upgrade4"]}', value="upgrade4"),
        Choice(name=f'Улучшение 5 - {loc.upgrade_name_dict["upgrade5"]}', value="upgrade5"),
        Choice(name=f'Улучшение 6 - {loc.upgrade_name_dict["upgrade6"]}', value="upgrade6"),
        Choice(name=f'Улучшение 7 - {loc.upgrade_name_dict["upgrade7"]}', value="upgrade7"),
    ])
    async def sell_upgrade(self, ctx: discord.Interaction, upgrade: str, quantity: int = 1):
        # Database connection and default value
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Upgrade - Help
        if upgrade == "help":
            # Info retrieval
            upg_lvl_data = sql_connection.execute(
                f"SELECT upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7 FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.user.id}").fetchone()
            sql_connection.close()

            # Reply embed
            any_fields_shown = False
            reply_embed = discord.Embed(title=f"Стоимость продажи улучшений для {ctx.user}",
                                        colour=discord.Colour.yellow())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            for i in range(len(upg_lvl_data)):
                if upg_lvl_data[i] != 0:
                    upgrade = f'upgrade{i + 1}'
                    reply_embed.add_field(
                        name=f"Цена улучшения {i + 1} - `{loc.upgrade_name_dict[upgrade]}` `{upg_lvl_data[i]}` уровня:",
                        value=f"🦚 {round(0.8 * loc.upgrade_prices_functions_dict[upgrade](upg_lvl_data[i]))}",
                        inline=False)
                    any_fields_shown = True

            if not any_fields_shown:
                reply_embed = discord.Embed(title=f"Стоимость продажи улучшений для {ctx.user}",
                                            description="Вам нечего продавать.",
                                            colour=discord.Colour.yellow())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_thumbnail(url=ctx.user.avatar)
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        upgrade_level = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, upgrade)
        upgrade_name = loc.upgrade_name_dict[upgrade]

        # Nothing to sell
        if upgrade_level == 0 or upgrade_level < quantity:
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Нечего продавать",
                                        description=f"<@{ctx.user.id}>, вы не можете продать уровень этого улучшения, "
                                                    f"так как вы не владеете им.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Calculate price
        if quantity < 1:
            quantity = 1
        sell_price = 0
        for i in range(upgrade_level, upgrade_level-quantity, -1):
            sell_price += round(loc.upgrade_prices_functions_dict[upgrade](i) * 0.8)

        # Update database
        sql_connection.execute(
            f"UPDATE ECONOMY SET {upgrade} = {upgrade_level - quantity} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, ctx.user.id))
        sql_connection.execute(
            f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {sell_price} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, ctx.user.id))

        # Close
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"✅ Успешная продажа",
                                    description=f"<@{ctx.user.id}> успешно продаёт {quantity} `{upgrade_name}` "
                                                f"за 🦚 {sell_price}.",
                                    colour=discord.Colour.green())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)

        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="steal", description="Украсть 🦚 из кошелька другого пользователя.")
    @app_commands.describe(member="Пользователь, у которого вы хотите украсть 🦚.",
                           lockpick="Использовать отмычку для взлома банка.")
    async def steal_peacocks(self, ctx: discord.Interaction, member: discord.Member, lockpick: bool = False):
        # Check if user is eligible
        if member.bot or ctx.user.id == member.id:
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Попробуйте другого пользователя.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Connection to database
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, member.id)

        # Check if there is theft cooldown
        last_theft_epoch = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "last_theft_attempt")
        epoch_right_now = int(time())

        # Theft
        if epoch_right_now < last_theft_epoch + loc.theft_cooldown:  # There is a cooldown
            # Close connection
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Попробуйте позже",
                                        description=f"<@{ctx.user.id}>, вы уже попытались ограбить пользователя ранее."
                                                    f" Попробуйте снова <t:{last_theft_epoch + 10 * 60}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        else:  # There is no cooldown
            # Check for lockpick
            target = "cookie_counter"
            place = ("Кошелёк", "кошельке")
            if lockpick:
                available_lockpicks = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "lockpicks")
                if available_lockpicks > 0:
                    target = "cookie_jar_storage"
                    place = ("Банк", "банке.\nОтмычка не была потрачена")
                    sql_connection.execute(
                        f"UPDATE ECONOMY SET lockpicks = lockpicks - 1 WHERE guild_id = ? AND user_id = ?",
                        (ctx.guild.id, ctx.user.id))
                else:
                    sql_connection.close()
                    # Reply embed
                    reply_embed = discord.Embed(title=f"❌ Нет отмычек",
                                                description=f"<@{ctx.user.id}>, у вас нет отмычек. "
                                                            f"Купите их в магазине: `/buy_items`.",
                                                colour=discord.Colour.red())
                    reply_embed.timestamp = loc.moscow_timezone()
                    reply_embed.set_footer(text=f"{ctx.guild.name}",
                                           icon_url=ctx.guild.icon)

                    return await ctx.response.send_message(embed=reply_embed, ephemeral=False)
            # Info retrieval
            target_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, member.id, target)
            author_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_counter")

            # Get percentages and cookies
            success_chance = randint(0, 100)
            cookies_stolen = loc.steal_cookies(target_cookies)
            cookies_lost_on_failure = loc.steal_cookies_failure(author_cookies)

            # Nothing to steal
            if cookies_stolen == 0:
                # refund lockpick
                if lockpick:
                    sql_connection.execute(
                        f"UPDATE ECONOMY SET lockpicks = lockpicks + 1 WHERE guild_id = ? AND user_id = ?",
                        (ctx.guild.id, ctx.user.id))
                # Close database
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ {place[0]} {member.name} пуст",
                                            description=f"<@{member.id}> не имеет 🦚 в {place[1]}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

            # Theft - success
            if success_chance >= 50:
                # Update database
                dbq.claim_peacock_bonus(sql_connection, ctx.guild.id, ctx.user.id, "last_theft_attempt", cookies_stolen,
                                        epoch_right_now)
                sql_connection.execute(
                    f"UPDATE ECONOMY SET last_robbed = {epoch_right_now} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, member.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET {target} = {target} - {cookies_stolen} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, member.id))
                sql_connection.commit()
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"🕵️ Успешное ограбление {member.name}: {place[0]}",
                                            description=f"<@{ctx.user.id}> украл 🦚 {cookies_stolen} у <@{member.id}>.",
                                            colour=discord.Colour.green())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

            # Theft - Failure
            elif success_chance in range(20, 50):
                # Close database
                dbq.claim_peacock_bonus(sql_connection, ctx.guild.id, ctx.user.id, "last_theft_attempt", 0,
                                        epoch_right_now)
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Неудачное ограбление {member.name}: {place[0]}",
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
                dbq.claim_peacock_bonus(sql_connection, ctx.guild.id, ctx.user.id, "last_theft_attempt",
                                        -cookies_lost_on_failure, epoch_right_now)
                # Close database
                sql_connection.close()

                # Reply embed
                reply_embed = discord.Embed(title=f"❌ Катастрофическое ограбление {member.name}: {place[0]}",
                                            description=f"Ограбление было предотвращено яростным вельш-корги.\n"
                                                        f"<@{ctx.user.id}> потерял 🦚 {cookies_lost_on_failure}.",
                                            colour=discord.Colour.red())
                reply_embed.timestamp = loc.moscow_timezone()
                reply_embed.set_footer(text=f"{ctx.guild.name}",
                                       icon_url=ctx.guild.icon)

                return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="deposit", description="Поместить 🦚 в банк.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите положить в банк.")
    async def save_peacocks_in_bank(self, ctx: discord.Interaction, amount: int):
        # Database connection
        sql_connection = sl.connect('Peacock.db')

        # Information retrieval
        author_bank_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_jar_storage")
        author_bank_level = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id,
                                                     "cookie_jar_storage_level")
        author_wallet = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_counter")

        # Target amount is more than you have in your wallet
        if amount > author_wallet:
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, вы не можете положить 🦚 {amount} в банк - "
                                                    f"у вас всего 🦚 {author_wallet} в вашем кошельке.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Not enough space in bank
        elif amount > author_bank_level * dbq.bank_capacity_per_lvl(ctx) - author_bank_cookies:
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно места в банке",
                                        description=f"<@{ctx.user.id}>, вы не можете положить 🦚 {amount} в банк - "
                                                    f"у вас есть место только для 🦚 {author_bank_level * dbq.bank_capacity_per_lvl(ctx) - author_bank_cookies} в вашем банке.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Everything is fine
        else:
            dbq.deposit_peacocks_in_bank(sql_connection, ctx.guild.id, ctx.user.id, amount)
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"🏦 Успешное пополнение банка",
                                        description=f"<@{ctx.user.id}> положил 🦚 {amount} в банк.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="withdraw", description="Забрать 🦚 из банка.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите забрать из банка.")
    async def withdraw_peacocks_from_bank(self, ctx: discord.Interaction, amount: int):
        # Database connection
        sql_connection = sl.connect('Peacock.db')

        # Information retrieval
        author_bank_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_jar_storage")

        # More demanded than in bank
        if amount > author_bank_cookies:
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств в банке",
                                        description=f"<@{ctx.user.id}>, вы не можете забрать 🦚 {amount} - "
                                                    f"у вас всего 🦚 {author_bank_cookies} в банке.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Everything is fine
        else:
            dbq.deposit_peacocks_in_bank(sql_connection, ctx.guild.id, ctx.user.id, -amount)
            # Close
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"🏦 Успешное изъятие средств из банка",
                                        description=f"<@{ctx.user.id}> забрал 🦚 {amount} из банка.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="work", description="Работа и получить 🦚 за приобретённые улучшения.")
    async def work(self, ctx: discord.Interaction):
        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Check if there is message cooldown
        last_access_epoch = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "last_access")
        fame_lvl = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "fame_lvl")
        epoch_right_now = int(time())

        if epoch_right_now < last_access_epoch + loc.work_bonus_cooldown:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Ошибка",
                                        description=f"Работа ещё не появилась. "
                                                    f"Вернитесь <t:{last_access_epoch + loc.work_bonus_cooldown}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Работа",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_thumbnail(url=ctx.user.avatar)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            # Calculate income
            gained_from_work = randint(250, 500)
            reply_embed.add_field(name=f"Доход от работы:",
                                  value=f"🦚 {gained_from_work}",
                                  inline=False)
            amount = gained_from_work
            for i in range(1, 8):
                upgrade = f'upgrade{i}'
                upgrade_level = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, upgrade)
                gain_per_level = loc.gain_from_upgrade_dict[upgrade]
                upgrade_income = round(gain_per_level * upgrade_level * (1+fame_lvl*0.02))

                amount += upgrade_income

                if upgrade_income > 0:
                    reply_embed.add_field(name=f"Доход от `{loc.upgrade_name_dict[upgrade]}`:",
                                          value=f"🦚 {upgrade_income} = {gain_per_level} x "
                                                f"{upgrade_income / gain_per_level}",
                                          inline=False)

            reply_embed.add_field(name="Итого:",
                                  value=f"Вы заработали 🦚 {amount}.",
                                  inline=False)
            # Update database
            dbq.claim_peacock_bonus(sql_connection, ctx.guild.id, ctx.user.id, "last_access", amount, epoch_right_now)
            sql_connection.close()

            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="ascend", description="Получить новый уровень карьеры.")
    @app_commands.describe(level_type="Категория уровня",
                           confirmation="Ваше согласие на повышение уровня.")
    @app_commands.choices(level_type=[
        Choice(name='Бизнесмен', value="fame_lvl"),
        # Choice(name='Пират', value="infamy_lvl"),
    ])
    async def ascend_level(self, ctx: discord.Interaction, level_type: str, confirmation: bool = False):
        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Database update
        level_name = 'Бизнесмен' if level_type == "fame_lvl" else 'Пират'

        if not confirmation:
            current_career_lvl = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, level_type)
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"Требования для повышение уровня карьеры: {level_name}",
                                        description=f"Для повышения уровня карьеры `{level_name}` вам необходимо "
                                                    f"использовать данную команду с опцией, "
                                                    f"дающей ваше согласие на повышение уровня, "
                                                    f"а также удовлетворять требованиям.",
                                        colour=discord.Colour.dark_green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            reply_embed.add_field(name=f'*ВНИМАНИЕ*',
                                  value=f'1) Все уровни улучшений будут обнулены.\n'
                                        f'2) Кошелёк будет обнулён.\n'
                                        f'3) Уровень банка и его содержимое останутся такими же.\n'
                                        f'4) Расходуемые предметы обнуляются.\n'
                                        f'\nРекомендуется продать улучшения выше указанного требования, '
                                        f'а также улучшить и заполнить банк.')
            if level_type == "fame_lvl":
                reply_embed.add_field(name=f'Требования следующего уровня `{level_name}`:',
                                      value=f'Уровень `{(current_career_lvl + 1) * loc.ascend_legal_path_min_lvls}` '
                                            f'во всех уровнях улучшений')
            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)
        else:
            # Check if eligible and nullify upgrades
            for i in range(1, 8):
                upgrade = f'upgrade{i}'
                current_upgrade_lvl = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, upgrade)
                current_career_lvl = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, level_type)
                if current_upgrade_lvl < (current_career_lvl + 1) * loc.ascend_legal_path_min_lvls:
                    # Close
                    sql_connection.close()
                    # Reply embed
                    reply_embed = discord.Embed(title=f"❌ Ошибка",
                                                description=f"<@{ctx.user.id}>, вы не удовлетворяете условиям "
                                                            f"для повышения уровня `{level_name}`.",
                                                colour=discord.Colour.red())
                    reply_embed.timestamp = loc.moscow_timezone()
                    reply_embed.set_footer(text=f"{ctx.guild.name}",
                                           icon_url=ctx.guild.icon)
                    return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

            for i in range(1, 8):
                upgrade = f'upgrade{i}'
                sql_connection.execute(
                    f"UPDATE ECONOMY SET {upgrade} = 0 WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.user.id))

            # Nullify wallet
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = 0 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))

            # Nullify items
            sql_connection.execute(
                f"UPDATE ECONOMY SET lockpicks = 0 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))

            # Level up
            sql_connection.execute(
                f"UPDATE ECONOMY SET {level_type} = {level_type} + 1 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            current_career_lvl = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, level_type)
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"Повышение уровня карьеры: {level_name}",
                                        description=f"Уровень `{level_name}` пользователя <@{ctx.user.id}> "
                                                    f"повышается до `{current_career_lvl}`!",
                                        colour=discord.Colour.dark_green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)
            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)


class peacockAdminEconomyCog(commands.GroupCog, name="adm_economy"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="edit_peacocks", description="Добавить/Забрать 🦚 пользователя.")
    @app_commands.describe(amount="Количество 🦚, которое вы хотите предоставить/забрать.",
                           target="Пользователь, чьи 🦚 будут изменены.")
    @app_commands.choices(where=[
        Choice(name='Кошелёк', value="cookie_counter"),
        Choice(name='Банк', value="cookie_jar_storage"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def edit_peacocks(self, ctx: discord.Interaction, target: discord.Member, where: str, amount: int):
        # Check if user is not a bot
        if target.bot:
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Попробуйте другого пользователя.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, target.id)

        # Info retrieval
        target_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, target.id, where)
        place = "Кошелёк" if where == "cookie_counter" else "Банк"
        operation = "Создание" if amount >= 0 else "Изъятие"
        verb = "создано" if amount >= 0 else "изъято"
        if target_cookies < abs(amount) and amount < 0:
            amount = target_cookies

        # Database update
        sql_connection.execute(
            f"UPDATE ECONOMY SET {where} = {where} + {amount} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, target.id))
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"{operation} валюты: {place}",
                                    description=f"🦚 {abs(amount)} было {verb} для <@{target.id}>",
                                    colour=discord.Colour.dark_green())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="set_career_level", description="Установить новый уровень карьеры для указанного пользователя.")
    @app_commands.describe(level_value="Значение нового уровня.",
                           target="Пользователь, чей уровень будем изменён.",
                           level_type="Категория уровня")
    @app_commands.choices(level_type=[
        Choice(name='Бизнесмен', value="fame_lvl"),
        Choice(name='Пират', value="infamy_lvl"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def set_career_level(self, ctx: discord.Interaction, target: discord.Member, level_type: str, level_value: int):
        # Check if user is not a bot
        if target.bot:
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Попробуйте другого пользователя.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, target.id)

        # Level can't be negative
        if level_value < 0:
            level_value = 0

        # Database update
        level_name = 'Бизнесмен' if level_type == "fame_lvl" else 'Пират'
        sql_connection.execute(
            f"UPDATE ECONOMY SET {level_type} = {level_value} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, target.id))
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"Изменение уровня карьеры: {level_name}",
                                    description=f"Уровень `{level_name}` пользователя <@{target.id}> "
                                                f"теперь равен `{level_value}`",
                                    colour=discord.Colour.yellow())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="set_upgrade_level", description="Установить новый уровень для указанного пользователя.")
    @app_commands.describe(level_value="Значение нового уровня.",
                           target="Пользователь, чей уровень будем изменён.",
                           upgrade_type="Категория улучшения")
    @app_commands.choices(upgrade_type=[
        Choice(name='Банк', value="cookie_jar_storage_level"),
        Choice(name=f'Улучшение 1 - {loc.upgrade_name_dict["upgrade1"]}', value="upgrade1"),
        Choice(name=f'Улучшение 2 - {loc.upgrade_name_dict["upgrade2"]}', value="upgrade2"),
        Choice(name=f'Улучшение 3 - {loc.upgrade_name_dict["upgrade3"]}', value="upgrade3"),
        Choice(name=f'Улучшение 4 - {loc.upgrade_name_dict["upgrade4"]}', value="upgrade4"),
        Choice(name=f'Улучшение 5 - {loc.upgrade_name_dict["upgrade5"]}', value="upgrade5"),
        Choice(name=f'Улучшение 6 - {loc.upgrade_name_dict["upgrade6"]}', value="upgrade6"),
        Choice(name=f'Улучшение 7 - {loc.upgrade_name_dict["upgrade7"]}', value="upgrade7"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def set_upgrade_level(self, ctx: discord.Interaction, target: discord.Member, upgrade_type: str, level_value: int):
        # Check if user is not a bot
        if target.bot:
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Попробуйте другого пользователя.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Сonnecting database
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, target.id)

        # Level can't be negative
        if level_value < 0:
            level_value = 0

        # Database update
        upgrade_name = loc.upgrade_name_dict[upgrade_type]
        sql_connection.execute(
            f"UPDATE ECONOMY SET {upgrade_type} = {level_value} WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, target.id))
        sql_connection.commit()
        sql_connection.close()

        # Reply embed
        reply_embed = discord.Embed(title=f"Изменение уровня улучшения: {upgrade_name}",
                                    description=f"Уровень `{upgrade_name}` пользователя <@{target.id}> "
                                                f"теперь равен `{level_value}`",
                                    colour=discord.Colour.yellow())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)
        return await ctx.response.send_message(embed=reply_embed, ephemeral=False)


class peacockEconomyShop(commands.GroupCog, name="shop"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_role", description="Купить роль за 🦚.")
    @app_commands.describe(role="Роль, которую вы купите за 🦚")
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
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Info retrieval
        author_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_counter")
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
                                        description=f"<@{ctx.user.id}>, вы не можете купить данную роль.\n"
                                                    f"Ваш кошелёк: 🦚 `{author_cookies}`\n"
                                                    f"Цена роли: 🦚 `{price}`.",
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

    @app_commands.command(name="remove_role", description="Убрать роль. Без возвратов 🦚.")
    @app_commands.describe(role="Роль, которую вы хотите убрать")
    @app_commands.choices(role=[
        Choice(name='Абонемент в архив грехов', value="role0"),
        Choice(name=f'Писарь грехов', value="role1"),
        Choice(name=f'Османский', value="role2"),
        Choice(name=f'Прусский', value="role3"),
        Choice(name=f'Нидерландский', value="role4"),
        Choice(name=f'Гордость', value="role5"),
        Choice(name=f'Who?', value="role6"),
    ])
    async def remove_role(self, ctx: discord.Interaction, role: str):
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
        # Role object
        role = discord.Object(role_id)

        # Take role
        await ctx.user.remove_roles(role, reason="Использовал слэш-команду, чтобы убрать роль.")

        # Reply embed
        reply_embed = discord.Embed(title=f"✅ Успеx",
                                    description=f"Роли <@{ctx.user.id}> успешно изменены.",
                                    colour=discord.Colour.green())
        reply_embed.timestamp = loc.moscow_timezone()
        reply_embed.set_footer(text=f"{ctx.guild.name}",
                               icon_url=ctx.guild.icon)

        return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

    @app_commands.command(name="timeout", description="Купить мут для участника сервера за 🦚.")
    @app_commands.describe(timeout_duration="Продолжительность мута", target="Участник, который получит мут.")
    @app_commands.choices(timeout_duration=[
        Choice(name='Убрать мут с участника', value=0),
        Choice(name='1 минута', value=1),
        Choice(name=f'10 минут', value=10),
        Choice(name=f'30 минут', value=30),
        Choice(name=f'1 час', value=60),
        Choice(name=f'24 часа', value=60 * 24),
    ])
    async def buy_timeout(self, ctx: discord.Interaction, target: discord.Member, timeout_duration: int):
        bot_top_role = ctx.guild.get_member(self.bot.user.id).top_role
        if target.bot or target.top_role > bot_top_role:  # Target is bot
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недопустимый пользователь",
                                        description=f"Попробуйте другого пользователя.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)

        # Database connection
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Info retrieval
        author_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_counter")
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
                                        description=f"<@{ctx.user.id}>, вы не можете купить данную услугу.\n"
                                                    f"Ваш кошелёк: 🦚 `{author_cookies}`\n"
                                                    f"Цена услуги: 🦚 `{price}`.",
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
                                        description=f"<@{ctx.user.id}> успешно приобретает мут для <@{target.id}> "
                                                    f"на `{timeout_duration}` минут за 🦚 {price}.",
                                        colour=discord.Colour.green()) if timeout_duration != 0 else discord.Embed(
                title=f"✅ Успешная покупка снятия мута для {target}",
                description=f"<@{ctx.user.id}> успешно приобретает снятие мута для <@{target.id}> за 🦚 {price}.",
                colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)

    @app_commands.command(name="buy_items", description="Купить расходуемые предметы за 🦚.")
    @app_commands.describe(item="Предмет, который вы купите.", quantity="Сколько будет куплено предметов")
    @app_commands.choices(item=[
        Choice(name=f'{loc.item_name_dict["lockpicks"]} (Позволяет ограбить банк 1 раз.)', value="lockpicks"),
    ])
    async def buy_item(self, ctx: discord.Interaction, item: str, quantity: int):
        # Database connection
        sql_connection = sl.connect('Peacock.db')
        dbq.add_new_user_to_economy_db(sql_connection, ctx.guild.id, ctx.user.id)

        # Info retrieval
        author_cookies = dbq.get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "cookie_counter")
        total_price = quantity * loc.item_dict[item]

        # Update database and reply
        if author_cookies >= total_price and quantity>0:
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {total_price} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET {item} = {item} + {quantity} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.user.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"✅ Успешная покупка предметов",
                                        description=f"<@{ctx.user.id}> успешно покупает `{loc.item_name_dict[item]}` "
                                                    f"в количестве {quantity} штук за 🦚 {total_price}.",
                                        colour=discord.Colour.green())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=False)
        else:
            sql_connection.close()
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Недостаточно средств",
                                        description=f"<@{ctx.user.id}>, вы не можете купить "
                                                    f"{quantity} штук `{loc.item_name_dict[item]}`.\n"
                                                    f"Ваш кошелёк: 🦚 {author_cookies}\n"
                                                    f"Вам необходимо: 🦚 {total_price}.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = loc.moscow_timezone()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon)

            return await ctx.response.send_message(embed=reply_embed, ephemeral=True)


async def setup(bot):
    sql_connection = sl.connect('Peacock.db')
    sql_connection.execute(
        f"CREATE TABLE IF NOT EXISTS ECONOMY (guild_id int, user_id int, "
        f"cookie_counter int, cookie_jar_storage int, cookie_jar_storage_level int, "
        f"upgrade1 int, upgrade2 int, upgrade3 int, upgrade4 int, upgrade5 int, upgrade6 int, upgrade7 int, "
        f"last_access int, daily_bonus int, weekly_bonus int, monthly_bonus int, message_cooldown int, "
        f"last_theft_attempt int, infamy_lvl int, fame_lvl int, last_robbed int, lockpicks int, "
        f"primary key (guild_id, user_id))")
    sql_connection.commit()
    sql_connection.close()
    await bot.add_cog(peacockEconomyCog(bot))
    await bot.add_cog(peacockAdminEconomyCog(bot))
    await bot.add_cog(peacockEconomyShop(bot))
