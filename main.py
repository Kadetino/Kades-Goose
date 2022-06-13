import discord  # Discord API wrapper
from discord import app_commands
from discord.ext import commands  # Discord BOT
import aiohttp  # For direct API requests and webhooks
import warnings  # For direct API requests and webhooks

from config import token, prefix, application_id, owners, webhookJoinLeave  # Global settings


# TODO Documentation / proper help command
class GooseBot(commands.Bot):

    def __init__(self):
        # Intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        # Constructor
        super().__init__(command_prefix=prefix, intents=intents, application_id=application_id,
                         owner_ids=set(owners))
        # Aiohttp
        self.session = aiohttp.ClientSession()

        # Cogs
        self.initial_extensions = [
            # "cogs.Lobby_finder_module",
            "cogs.event_module",
            # "cogs.EU4Ideas_module",
            "cogs.misc",
            "cogs.peacock_economy",
            "cogs.Duel_module",
        ]

        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            """Error handler"""
            if isinstance(error, app_commands.MissingPermissions):
                return await interaction.response.send_message(str(error), ephemeral=True)
            else:
                print(str(error))
                return await interaction.response.send_message("Unknown error.", ephemeral=True)

    async def setup_hook(self):
        # Cogs
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        # Slash commands - Goose refuge
        self.tree.copy_global_to(guild=discord.Object(id=950688544433778689))
        await self.tree.sync(guild=discord.Object(id=950688544433778689))
        # # Slash commands
        # self.tree.copy_global_to(guild=discord.Object(id=664124313997148170))
        # await self.tree.sync(guild=discord.Object(id=664124313997148170))

    async def close(self):
        await super().close()
        await self.session.close()

    async def on_ready(self):
        print('Logged on as {0.user}!'.format(bot))
        # await bot.change_presence(activity=discord.Game(name="Honk! Honk!"))



    async def on_guild_join(self, guild):
        """Send to goose server webhook, which servers bot has joined."""
        # Webhook
        webhook = discord.Webhook.from_url(webhookJoinLeave, session=self.session)
        # Discord embed
        server_embed = discord.Embed(title="New server!", description=f'{bot.user.name} has been added to: {guild}',
                                     colour=discord.Colour.green())
        server_embed.set_thumbnail(url=guild.icon)

        return await webhook.send(embed=server_embed, username="Overseer")  # Executing webhook.

    async def on_guild_remove(self, guild):
        """Send to goose server webhook, which servers bot has left."""
        # Webhook
        webhook = discord.Webhook.from_url(webhookJoinLeave, session=self.session)
        # Discord embed
        server_embed = discord.Embed(title="Farewell...",
                                     description=f'{bot.user.name} has left: {guild}',
                                     colour=discord.Colour.red())
        server_embed.set_thumbnail(url=guild.icon)

        return await webhook.send(embed=server_embed, username="Overseer")  # Executing webhook.


warnings.filterwarnings("ignore", category=DeprecationWarning)
bot = GooseBot()
bot.remove_command('help')

bot.run(token)
