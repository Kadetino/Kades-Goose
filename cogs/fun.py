import discord
from discord.ext import commands
import datetime
import random
import sqlite3 as sl

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def timeout_user(self, *, user_id: int, guild_id: int, until):
        headers = {"Authorization": f"Bot {self.bot.http.token}"}
        url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}"
        timeout = (datetime.datetime.utcnow() + datetime.timedelta(minutes=until)).isoformat()
        json = {'communication_disabled_until': timeout}
        async with self.bot.session.patch(url, json=json, headers=headers) as session:
            if session.status in range(200, 299):
               return True
            return False


    @commands.command()
    async def shootout(self,ctx: commands.Context, member: discord.Member):
        con = sl.connect('Goose.db')
        con.execute(
            "CREATE TABLE IF NOT EXISTS DUELDATA (guild_id int, user_id int, wins int, loses int, PRIMARY KEY (guild_id, user_id))")

        success_chance = random.randint(0, 100)
        critical_failure_chance = random.randint(0, 100)
        default_punish_time = 5
        critical_failure_punsih_time = 60
        protectedusers = [231388394360537088,912349700416479292]
        voice_state_defender = member.voice


        if member.id in protectedusers: # Kade and Goose never lose
            muted_user = ctx.author
            winner_user = member
            handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=default_punish_time)
            await ctx.reply(f"{muted_user} loses.")
        # elif ctx.guild.id==429614832447127552 and ctx.channel.id!=950455558320836678:
        #     muted_user = ctx.author
        #     winner_user = member
        #     handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=1)
        #     await ctx.reply(f"{muted_user} loses. <:JabkaJopoZashishatelnica:594112176482942976> Luck is increased in duel chat.")
        elif success_chance<=66 and voice_state_defender is None: # Attacker wins.
            muted_user = member
            winner_user = ctx.author
            handshake = await self.timeout_user(user_id=member.id, guild_id=ctx.guild.id, until=default_punish_time)
            await ctx.reply(f"{muted_user} loses.")
        else: # Attacker loses
            muted_user = ctx.author
            winner_user = member
            if critical_failure_chance<=97: # Critical failure check
                handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=default_punish_time)
                await ctx.reply(f"{muted_user} loses.")
            else:
                handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=critical_failure_punsih_time)
                await ctx.reply(f"{muted_user} shotguns himself.")

        if handshake:
            print(f"{ctx.guild.name} - Successfully timed out {muted_user} in {ctx.author} vs {member} fight.")
        else:
            print(f"{ctx.guild.name} - Something went wrong: couldn't time out {muted_user} in {ctx.author} vs {member} fight.")

        if not ctx.author.bot and not member.bot:
            # New entry, if user didn't use duel before on this server
            cursor = con.execute("INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses) VALUES (?,?,0,1)",(ctx.guild.id, muted_user.id))
            # Update loses for the loser
            if cursor.rowcount == 0:
                con.execute("UPDATE DUELDATA SET loses = loses + 1 WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, muted_user.id))
            # New entry, if user didn't use duel before on this server
            cursor = con.execute("INSERT OR IGNORE INTO DUELDATA (guild_id, user_id, wins, loses) VALUES (?,?,1,0)",(ctx.guild.id, winner_user.id))
            # Update wins for the winner
            if cursor.rowcount == 0:
                con.execute("UPDATE DUELDATA SET wins = wins + 1 WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, winner_user.id))
        # save changes
        con.commit()
        con.close()

    @commands.command()
    async def stats(self,ctx, member: discord.Member = None):
        if member is None: member = ctx.author
        #
        # # get user exp
        # async with bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ? AND user_id = ?",
        #                           (ctx.guild.id, member.id)) as cursor:
        #     data = await cursor.fetchone()
        #     exp = data[0]
        #
        #     # calculate rank
        # async with bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
        #     rank = 1
        #     async for value in cursor:
        #         if exp < value[0]:
        #             rank += 1
        #
        # lvl_percentage = ((exp - current_lvl_exp) / (next_lvl_exp - current_lvl_exp)) * 100
        #
        # embed = discord.Embed(title=f"Stats for {member.name}", colour=discord.Colour.gold())
        # embed.add_field(name="Level", value=str(lvl))
        # embed.add_field(name="Exp", value=f"{exp}/{next_lvl_exp}")
        # embed.add_field(name="Rank", value=f"{rank}/{ctx.guild.member_count}")
        # embed.add_field(name="Level Progress", value=f"{round(lvl_percentage, 2)}%")
        #
        # await ctx.send(embed=embed)
def setup(bot):
    bot.add_cog(FunCog(bot))