import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT


class EU4IdeasCog(commands.Cog):
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


def setup(bot):
    bot.add_cog(EU4IdeasCog(bot))
