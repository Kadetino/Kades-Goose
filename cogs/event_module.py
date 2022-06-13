import discord  # Discord API wrapper
from discord import app_commands
from discord.ext import commands  # Discord BOT


class eventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def on_message_add_reactions(self, user_message: discord.message.Message):
        # TODO Regex
        # Checks if user is not a bot
        if user_message.author.bot:
            return
        if "москва" or "москов" in str(user_message.content):
            await user_message.add_reaction("<:Moskivskiye_vpered:948545104560402432>")
        if "коромел" or "карамель" or "карач" in str(user_message.content):
            await user_message.add_reaction("<:ukrjabka:797774103212982323>")
        if "кайф" or "каеф" in str(user_message.content):
            await user_message.add_reaction("<:Karamel_sgorel:795629475487809546>")
        if "запрещаю" in str(user_message.content):
            await user_message.add_reaction("<:Zapreshayu_Greshit:739497647433580605>")
        if "больно" in str(user_message.content):
            await user_message.add_reaction("<:opyat_na_zavod:822447343902523403>")
        if "кайзер" in str(user_message.content):
            await user_message.add_reaction("<:kaizer:977185604959866914>")
        if "русский" in str(user_message.content):
            await user_message.add_reaction("<:Gott_mit_uns:821776425950248990>")
        if "не бывает" in str(user_message.content):
            await user_message.add_reaction("<:Pomoiniy_Greh:769535867366670347>")
        if "факторио" or "завод" in str(user_message.content):
            await user_message.add_reaction("<:Izbavilsya_ot_greshnika:800791792956997653>")
            await user_message.add_reaction("🏭")


async def setup(bot):
    await bot.add_cog(eventCog(bot))
