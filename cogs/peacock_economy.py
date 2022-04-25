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
            "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
            (user_message.guild.id, user_message.author.id))

        # Check if there is message cooldown
        database_entry = sql_connection.execute(
            f"SELECT message_cooldown FROM ECONOMY WHERE guild_id = {user_message.guild.id} AND user_id = {user_message.author.id}").fetchone()
        epoch_timestamp_right_now = int(time())
        if epoch_timestamp_right_now < database_entry[0] + 10:
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
            storage.append((f"{user.name}#{user.discriminator}", total_peacocks))
            # Save variable if it was the author
            if ctx.author.id == line[0]:
                author_entry = f"Your position: `#{len(storage)}` {user.name}#{user.discriminator}: 🦚 {total_peacocks}"

        # Sort storage for leaderboard
        storage.sort(key=lambda y: y[1], reverse=True)

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
                        value=f"description",
                        inline=False)

        return await ctx.reply(embed=embed)


def setup(bot):
    sql_connection = sl.connect('Goose.db')
    sql_connection.execute(
        f"CREATE TABLE IF NOT EXISTS ECONOMY (guild_id int, user_id int, cookie_counter int, cookie_jar_storage int, cookie_jar_storage_level int, upgrade1 int, upgrade2 int, upgrade3 int, upgrade4 int, upgrade5 int, upgrade6 int, upgrade7 int, last_access int, daily_bonus int, weekly_bonus int, monthly_bonus int, message_cooldown int, primary key (guild_id, user_id))")
    sql_connection.close()
    bot.add_cog(peacockEconomyCog(bot))
