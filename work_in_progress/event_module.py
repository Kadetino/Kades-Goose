import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
from discord import Webhook, AsyncWebhookAdapter  # Importing discord.Webhook and discord.AsyncWebhookAdapter

import config  # Global settings


class eventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Send to goose server webhook, which servers bot joined."""
        # Webhook
        webhook = Webhook.from_url(config.webhookJoinLeave, adapter=AsyncWebhookAdapter(self.bot.session))  # Initializing webhook with AsyncWebhookAdapter
        # Discord embed
        server_embed = discord.Embed(title="New server!", description=f'Bot has been added to: {guild}', colour=discord.Colour.green())
        server_embed.set_thumbnail(url=guild.icon_url)

        return await webhook.send(embed=server_embed, username="Goose Overseer")  # Executing webhook.


    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Send to goose server webhook, which servers bot left."""
        # Webhook
        webhook = Webhook.from_url(config.webhookJoinLeave, adapter=AsyncWebhookAdapter(self.bot.session))  # Initializing webhook with AsyncWebhookAdapter
        # Discord embed
        server_embed = discord.Embed(title="Farewell...", description=f'Bot has left: {guild}', colour=discord.Colour.red())
        server_embed.set_thumbnail(url=guild.icon_url)

        return await webhook.send(embed=server_embed, username="Goose Overseer")  # Executing webhook.


async def setup(bot):
    await bot.add_cog(eventCog(bot))
