import discord  # Discord API wrapper
from discord import app_commands
from discord.ext import commands  # Discord BOT

# class buttonHandler(discord.ui.View):
#     @discord.ui.button(label="yepa",
#                        style=discord.ButtonStyle.success,
#                        emoji="🏭")
#     async def button(self, interaction:discord.Interaction,button:discord.ui.Button):
#         await interaction.response.edit_message(content="OOOOO")


class utilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="support_bot", description="Информация о том, как поддержать бота.")
    async def supportGoose(self, ctx: discord.Interaction):
        support_embed = discord.Embed(title="Поддержать бота!",
                                      description="Если вам нравится бот и вы хотите его поддержать, "
                                                  "то вот как это можно сделать.",
                                      colour=discord.Colour.gold())
        # support_embed.add_field(name=f"`Metamask`", value="0xe2d321ebb477d14d2d38D97c9d2D39dC97A262Eb", inline=False)
        support_embed.set_thumbnail(url=self.bot.user.avatar)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Qiwi",
                                        url="https://qiwi.com/n/CLUST224",
                                        emoji="🥝"))
        view.add_item(discord.ui.Button(label="Ko-fi",
                                        url="https://ko-fi.com/kadetino",
                                        emoji="☕"))

        return await ctx.response.send_message(embed=support_embed, view=view)

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
        guild_embed = discord.Embed(title=f'{self.bot.user} Guilds', description=f"Total: {len(self.bot.guilds)} guilds.", color=discord.Colour.gold())
        for guild in self.bot.guilds:
            guild_embed.add_field(name=f'`{guild.name}`', value=guild.id, inline=False)
        return await ctx.reply(embed=guild_embed)


async def setup(bot):
    await bot.add_cog(utilityCog(bot))
