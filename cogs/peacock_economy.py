import datetime  # Timestamps in embeds

import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
from random import randint  # Random number generation for economy
from config import prefix, cd_commands  # Global settings
from time import time  # Epoch timestamp


class peacockEconomyCog(commands.Cog):
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

    @commands.command(name="leaderboard", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def economyboard(self, ctx: commands.Context):
        # Init
        sql_connection = sl.connect('Goose.db')

        # Get data and close
        data = sql_connection.execute(
            f"select user_id, cookie_counter, cookie_jar_storage from ECONOMY where guild_id = {ctx.guild.id}").fetchall()
        sql_connection.close()

        # Check if data is empty
        if len(data) == 0:
            return await ctx.reply("Nothing to show.")

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
            if storage[i][0] == str(ctx.author):
                author_entry = f"Your position: `#{i + 1}` {ctx.author}: 🦚 {storage[i][1]}"
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
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name=f"❓ How it works?",
                        value=f"You get 🦚 for your messages, `{prefix}daily`, `{prefix}weekly` or `{prefix}monthly`. Bonus points if you user 🦚 emoji in your messages!",
                        inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"{ctx.author}",
                         icon_url=ctx.author.avatar_url)

        return await ctx.reply(embed=embed)

    @commands.command(name="give", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def transfer_peacocks(self, ctx: commands.Context, target_member: discord.Member, target_amount: int):
        # Checks if target is valid member
        if target_member.bot:  # Target is a bot
            reply_embed = discord.Embed(title=f"❌ Invalid target",
                                        description=f"Bots are not humans. (...yet)",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)
        elif ctx.author.id == target_member.id:  # Target is yourself
            reply_embed = discord.Embed(title=f"❌ Invalid target",
                                        description=f"You mentioned yourself.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)

        # Connection to database and retrieving authors peacocks
        sql_connection = sl.connect('Goose.db')
        author_cookies = sql_connection.execute(
            f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()[
            0]

        # Check if author has sufficien amount of peacocks
        if author_cookies < round(target_amount * 1.05) + 1:  # He doesn't have enough
            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Not enough peacocks",
                                        description=f"{ctx.author.name}#{ctx.author.discriminator}, you have inssufficient amount of peacocks to transfer.\nYou have 🦚 {author_cookies} and and there is 5% 🦚 commision fee",
                                        colour=discord.Colour.red())
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)

            # Close connection and reply
            sql_connection.close()

            return await ctx.reply(embed=reply_embed)
        else:  # Author has enough
            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Successful transfer",
                                        description=f"Successcully transfered 🦚 {target_amount} from {ctx.author.name}#{ctx.author.discriminator} to {target_member.name}#{target_member.discriminator}.\n\nCommission was 5% 🦚.",
                                        colour=discord.Colour.green())
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)

            # Add user to database if he wasn't there before
            sql_connection.execute(
                "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
                (ctx.guild.id, target_member.id))

            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {target_amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            if round(target_amount * 0.05) == 0:
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - 1 WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
            else:
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {round(target_amount * 0.05)} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {target_amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, target_member.id))
            sql_connection.commit()
            sql_connection.close()

            return await ctx.reply(embed=reply_embed)

    @commands.command(name="buy_upgrade", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def buy_upgrade(self, ctx: commands.Context, target_upgrade: str, target_quantity: int = 1):
        # TODO
        sql_connection = sl.connect("Goose.db")
        data = sql_connection.execute(
            f"SELECT cookie_counter, cookie_jar_storage_level FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()
        author_cookies = data[0]
        bank_level = data[1]
        if target_upgrade == "bank":
            bank_level_price = 200 * 2 ** bank_level
            if author_cookies < bank_level_price:
                return await ctx.reply(
                    f"❌ {ctx.author}, not enough 🦚 to buy bank level.\nYou have: 🦚 {author_cookies}\nBank level `{bank_level + 1}` price: 🦚 {bank_level_price}")
            else:
                bank_level += 1
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_jar_storage_level = {bank_level} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {bank_level_price} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
                sql_connection.commit()
                sql_connection.close()
                return await ctx.reply(
                    f"Successfuly bought: `Bank level {bank_level}` for 🦚 {bank_level_price}.\n{ctx.author} bank capacity is now 🦚 {bank_level * 400}.")
        else:
            return

    @commands.command(name="sell_upgrade", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def sell_upgrade(self, ctx: commands.Context, target_upgrade: str, target_quantity: int):
        # TODO
        return

    @commands.command(name="steal", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def steal_peacocks(self, ctx: commands.Context, target_member: discord.Member):
        # TODO
        if ctx.author.id == target_member.id:  # Target is yourself
            reply_embed = discord.Embed(title=f"❌ Invalid target",
                                        description=f"You can't steal from yourself.",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)

        # Connection to database
        sql_connection = sl.connect('Goose.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, target_member.id))

        # Check if there is theft cooldown
        last_attempted_theft_epoch = sql_connection.execute(
            f"SELECT last_theft_attempt FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()[0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_attempted_theft_epoch + 10 * 60:  # There is a cooldown
            sql_connection.close()
            return await ctx.reply(f"{ctx.author}, you have attempted theft before. Try again <t:{last_attempted_theft_epoch + 10 * 60}:R>")
        else:  # There is no cooldown - set a new one
            # Get info from database
            target_cookies = sql_connection.execute(
                f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {target_member.id}").fetchone()[
                0]
            author_cookies = sql_connection.execute(
                f"SELECT cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()[
                0]
            success_chance = randint(0, 100)
            cookies_stolen = int(randint(5, 65)/100 * target_cookies)
            cookies_lost_on_failure = int(randint(5, 15)/100 * author_cookies)
            if cookies_stolen == 0:
                sql_connection.commit()
                sql_connection.close()
                return await ctx.reply(f"{target_member} has nothing to steal. Theft cooldown unaffected.")
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET last_theft_attempt = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.commit()
            # Theft
            if success_chance >= 50:
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {cookies_stolen} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {cookies_stolen} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, target_member.id))
                sql_connection.commit()
                sql_connection.close()
                return await ctx.reply(f"{ctx.author} stole 🦚 {cookies_stolen} from {target_member}.")
            elif success_chance in range(20, 50):
                sql_connection.close()
                return await ctx.reply(f"{ctx.author} was scared and didn't steal anything from {target_member}.")
            else:
                if author_cookies < cookies_lost_on_failure:
                    cookies_lost_on_failure = author_cookies
                sql_connection.execute(
                    f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {cookies_lost_on_failure} WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, ctx.author.id))
                sql_connection.commit()
                sql_connection.close()
                return await ctx.reply(
                    f"{ctx.author} heroic theft attempt was interrupted by ferocious Welsh Corgi.\n{ctx.author} lost 🦚 {cookies_lost_on_failure}.")

    @commands.command(name="balance", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def display_user_profile(self, ctx: commands.Context, target_member: discord.Member = None):
        # TODO
        if target_member is None:
            target_member = ctx.author
        sql_connection = sl.connect("Goose.db")
        data = sql_connection.execute(
                f"SELECT cookie_counter, cookie_jar_storage_level, cookie_jar_storage FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {target_member.id}").fetchone()
        author_cookies = data[0]
        bank_level = data[1]
        bank_deposit = data[2]
        sql_connection.close()
        return await ctx.reply(
            f"{target_member} has 🦚 {author_cookies} in their wallet and 🦚 {bank_deposit}/{bank_level * 400} in their bank.")

    @commands.command(name="daily", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def daily_bonus(self, ctx: commands.Context):
        # Checks and connecting database
        if ctx.author.bot:
            return
        sql_connection = sl.connect('Goose.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.author.id))

        # Check if there is message cooldown
        last_daily_bonus_received_epoch = sql_connection.execute(
            f"SELECT daily_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_daily_bonus_received_epoch + 24 * 3600:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Daily bonus",
                                        description=f"You have already claimed your daily bonus. Come back <t:{last_daily_bonus_received_epoch + 24 * 3600}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)
        else:
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET daily_bonus = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + 400 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Daily bonus",
                                        description=f"You have claimed your daily 🦚 400 bonus.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)

    @commands.command(name="weekly", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def weekly_bonus(self, ctx: commands.Context):
        # Checks and connecting database
        if ctx.author.bot:
            return
        sql_connection = sl.connect('Goose.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.author.id))

        # Check if there is message cooldown
        last_weekly_bonus_received_epoch = sql_connection.execute(
            f"SELECT weekly_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_weekly_bonus_received_epoch + 7 * 24 * 3600:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Weekly bonus",
                                        description=f"You have already claimed your weekly bonus. Come back <t:{last_weekly_bonus_received_epoch + 7 * 24 * 3600}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)
        else:
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET weekly_bonus = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + 750 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Weekly bonus",
                                        description=f"You have claimed your weekly 🦚 750 bonus.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)

    @commands.command(name="monthly", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def monthly_bonus(self, ctx: commands.Context):
        # Checks and connecting database
        if ctx.author.bot:
            return
        sql_connection = sl.connect('Goose.db')

        # Add user to database if he wasn't there before
        sql_connection.execute(
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (ctx.guild.id, ctx.author.id))

        # Check if there is message cooldown
        last_weekly_bonus_received_epoch = sql_connection.execute(
            f"SELECT monthly_bonus FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()[
            0]
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < last_weekly_bonus_received_epoch + 30 * 24 * 3600:
            # Close connection
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"❌ Monthly bonus",
                                        description=f"You have already claimed your monthly bonus. Come back <t:{last_weekly_bonus_received_epoch + 30 * 24 * 3600}:R>",
                                        colour=discord.Colour.red())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)
        else:
            # Update database
            sql_connection.execute(
                f"UPDATE ECONOMY SET monthly_bonus = {epoch_timestamp_right_now} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + 1500 WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.commit()
            sql_connection.close()

            # Reply embed
            reply_embed = discord.Embed(title=f"💰 Monthly bonus",
                                        description=f"You have claimed your monthly 🦚 1500 bonus.",
                                        colour=discord.Colour.gold())
            reply_embed.timestamp = datetime.datetime.utcnow()
            reply_embed.set_thumbnail(url=ctx.author.avatar_url)
            reply_embed.set_footer(text=f"{ctx.guild.name}",
                                   icon_url=ctx.guild.icon_url)
            return await ctx.reply(embed=reply_embed)

    @commands.command(name="deposit", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def save_peacocks_in_bank(self, ctx: commands.Context, target_amount: int):
        # TODO
        sql_connection = sl.connect("Goose.db")
        data = sql_connection.execute(
            f"SELECT cookie_jar_storage, cookie_jar_storage_level, cookie_counter FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()
        author_bank_cookies = data[0]
        author_bank_level = data[1]
        author_wallet = data[2]
        if target_amount > author_wallet:
            return await ctx.reply(
                f"❌ {ctx.author}, you can't deposit 🦚 {target_amount} - you only have 🦚 {author_wallet} in your wallet.")
        elif target_amount > author_bank_level * 400 - author_bank_cookies:
            sql_connection.close()
            return await ctx.reply(
                f"❌ {ctx.author}, you can't deposit 🦚 {target_amount} - you only have space for 🦚 {author_bank_level * 400 - author_bank_cookies} in your bank.")
        else:
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {target_amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_jar_storage = cookie_jar_storage + {target_amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.commit()
            sql_connection.close()
            return await ctx.reply(f"{ctx.author} made a deposit of 🦚 {target_amount} to their local bank.")

    @commands.command(name="withdraw", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def withdraw_peacocks_from_bank(self, ctx: commands.Context, target_amount: int):
        # TODO
        sql_connection = sl.connect("Goose.db")
        author_bank_cookies = sql_connection.execute(
            f"SELECT cookie_jar_storage FROM ECONOMY WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}").fetchone()[0]
        if target_amount > author_bank_cookies:
            sql_connection.close()
            return await ctx.reply(f"❌ {ctx.author}, you can't withdraw 🦚 {target_amount} - you only have 🦚 {author_bank_cookies} in your bank.")
        else:
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {target_amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.execute(
                f"UPDATE ECONOMY SET cookie_jar_storage = cookie_jar_storage - {target_amount} WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, ctx.author.id))
            sql_connection.commit()
            sql_connection.close()
            return await ctx.reply(f"{ctx.author} withdrew 🦚 {target_amount} from their bank account.")

    @commands.command(name="work", pass_context=True)
    @commands.cooldown(1, cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def work_on_plantations(self, ctx: commands.Context):
        # TODO and maybe increase command cooldown. and include upgrade calculation here
        return


def setup(bot):
    sql_connection = sl.connect('Goose.db')
    sql_connection.execute(
        f"CREATE TABLE IF NOT EXISTS ECONOMY (guild_id int, user_id int, cookie_counter int, cookie_jar_storage int, cookie_jar_storage_level int, upgrade1 int, upgrade2 int, upgrade3 int, upgrade4 int, upgrade5 int, upgrade6 int, upgrade7 int, last_access int, daily_bonus int, weekly_bonus int, monthly_bonus int, message_cooldown int, last_theft_attempt int, primary key (guild_id, user_id))")
    sql_connection.close()
    bot.add_cog(peacockEconomyCog(bot))
