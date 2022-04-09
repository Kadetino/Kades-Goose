import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT


class utilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def supportGoose(self, ctx: commands.Context):
        """Bot command with information about ways on how to support Goose development."""

        message = "If you like the bot, consider supporting us!"
        support_embed = discord.Embed(title="Support the Goose!", description=message, colour=discord.Colour.gold())
        support_embed.add_field(name=f"`Ko-fi`", value="https://ko-fi.com/kadetino", inline=False)
        support_embed.add_field(name=f"`Metamask`", value="0xe2d321ebb477d14d2d38D97c9d2D39dC97A262Eb", inline=False)
        return await ctx.reply(embed=support_embed)

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        """Stop the Goose"""
        await ctx.reply("Shutting down, Master.")
        await self.bot.session.close()
        return await ctx.bot.close()

    @commands.command()
    @commands.is_owner()
    async def leave(self, ctx: commands.Context, guild_id: int):
        """Leave the specified guild."""
        await self.bot.get_guild(int(guild_id)).leave()
        return await ctx.reply(f"I left: {guild_id}")

    @commands.command()
    @commands.is_owner()
    async def showguilds(self, ctx):
        """List all guilds' bot is a part of."""
        guild_embed = discord.Embed(title=f'{self.bot.user} Guilds', color=discord.Colour.gold())
        for guild in self.bot.guilds:
            guild_embed.add_field(name=f'`{guild.name}`', value=guild.id, inline=False)
        return await ctx.reply(embed=guild_embed)


def setup(bot):
    bot.add_cog(utilityCog(bot))
