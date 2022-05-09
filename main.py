import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import aiohttp  # For direct API requests and webhooks
import warnings  # For direct API requests and webhooks

from config import token, prefix, application_id, owners  # Global settings


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
            # "cogs.event_module",
            # "cogs.EU4Ideas_module",
            "cogs.misc",
            "cogs.peacock_economy"
        ]

    async def setup_hook(self):
        # Cogs
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        # Slash commands - Goose refuge
        self.tree.copy_global_to(guild=discord.Object(id=950688544433778689))
        await self.tree.sync(guild=discord.Object(id=950688544433778689))
        # Slash commands
        self.tree.copy_global_to(guild=discord.Object(id=664124313997148170))
        await self.tree.sync(guild=discord.Object(id=664124313997148170))

    async def close(self):
        await super().close()
        await self.session.close()

    async def on_ready(self):
        print('Logged on as {0.user}!'.format(bot))
        await bot.change_presence(activity=discord.Game(name="Honk! Honk!"))


warnings.filterwarnings("ignore", category=DeprecationWarning)
bot = GooseBot()
bot.run(token)
bot.remove_command('help')  # help command probably needs to be reworked

# For Duels and webhooks
# warnings.filterwarnings("ignore", category=DeprecationWarning)
# bot.session = aiohttp.ClientSession()
