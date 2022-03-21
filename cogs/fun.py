import discord
from discord.ext import commands
import datetime
import random

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
        success_chance = random.randint(0, 100)
        critical_failure_chance = random.randint(0, 100)
        default_punish_time = 5
        critical_failure_punsih_time = 60
        protectedusers = [231388394360537088,912349700416479292]
        voice_state_defender = member.voice

        if member.id in protectedusers: # Kade and Goose never lose
            muted_user = ctx.author
            handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=default_punish_time)
            await ctx.reply(f"{muted_user} loses.")
        elif ctx.guild.id==429614832447127552 and ctx.channel.id!=950455558320836678:
            muted_user = ctx.author
            handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=1)
            await ctx.reply(f"{muted_user} loses. <:JabkaJopoZashishatelnica:594112176482942976> Luck is increased in duel chat.")
        elif success_chance<=66 and voice_state_defender is None: # Attacker wins.
            muted_user = member
            handshake = await self.timeout_user(user_id=member.id, guild_id=ctx.guild.id, until=default_punish_time)
            await ctx.reply(f"{muted_user} loses.")
        else: # Attacker loses
            muted_user = ctx.author
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


def setup(bot):
    bot.add_cog(FunCog(bot))