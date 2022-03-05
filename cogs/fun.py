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
        target = random.randint(0, 2)
        protectedusers = [231388394360537088,912349700416479292]

        if member.id in protectedusers: # Kade and Goose never lose
            muted_user = ctx.author
            handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=1)
        elif target!=1:
            muted_user = member
            handshake = await self.timeout_user(user_id=member.id, guild_id=ctx.guild.id, until=1)
        else:
            muted_user = ctx.author
            handshake = await self.timeout_user(user_id=ctx.author.id, guild_id=ctx.guild.id, until=1)

        await ctx.reply(f"{muted_user} loses.")
        if handshake:
            print(f"shootout - Successfully timed out {muted_user} for 1 minute by {ctx.author}.")
        else:
            print(f"shootout - Something went wrong: couldn't time out {muted_user}.")


def setup(bot):
    bot.add_cog(FunCog(bot))