import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT

import config  # Global settings


class eventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    #     self.session = bot.session
    #
    # @commands.Cog.listener()
    # async def on_guild_join(self, guild):
    #     """Send to goose server webhook, which servers bot joined."""
    #     # Webhook
    #     webhook = discord.Webhook.from_url(config.webhookJoinLeave, session=self.session)
    #     # Discord embed
    #     server_embed = discord.Embed(title="New server!", description=f'Bot has been added to: {guild}', colour=discord.Colour.green())
    #     server_embed.set_thumbnail(url=guild.icon)
    #
    #     return await webhook.send(embed=server_embed, username="Overseer")  # Executing webhook.


    # @commands.Cog.listener()
    # async def on_guild_remove(self, guild):
    #     """Send to goose server webhook, which servers bot left."""
    #     # Webhook
    #     webhook = discord.Webhook.from_url(config.webhookJoinLeave, session=self.session)
    #     # Discord embed
    #     server_embed = discord.Embed(title="Farewell...", description=f'Bot has left: {guild}', colour=discord.Colour.red())
    #     server_embed.set_thumbnail(url=guild.icon)
    #
    #     return await webhook.send(embed=server_embed, username="Overseer")  # Executing webhook.


async def setup(bot):
    await bot.add_cog(eventCog(bot))
