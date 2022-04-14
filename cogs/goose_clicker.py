import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database
import asyncio

class clickerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')

    async def on_mssessage(self,ctx):
        # if message.content.startswith('click'):
        if ctx.content.startswith('click'):
            return await ctx.reply("peepoopee")
            channel = message.channel
            await channel.send('Obtained 1 goose-cookie')

            # Init
            con = sl.connect('Goose.db')

            member = message.author.id

            #if member is None:
            #    member = ctx.author
            con.execute("INSERT OR IGNORE INTO CLICKER (guild_id, user_id, cookie_counter, upgrade1, last_access) VALUES (?,?,0,0,0)",
                        (message.author.id.guild.id, member.id))
            # Retrieve cookies
            data = con.execute("SELECT cookie_counter FROM CLICKER WHERE guild_id = ? AND user_id = ?",
                               (message.author.id.guild.id, member.id)).fetchone()
            cookies = data[0]
            # Retrive upgrades
            data = con.execute("SELECT upgrade1 FROM CLICKER WHERE guild_id = ? AND user_id = ?",
                               (message.author.id.guild.id, member.id)).fetchone()
            upgrades = data[0]
            # Retrive last access
            data = con.execute("SELECT last_access FROM CLICKER WHERE guild_id = ? AND user_id = ?",
                               (message.author.id.guild.id, member.id)).fetchone()
            optout = data[0]
            # Close connection
            con.commit()
            con.close()


def setup(bot):
    bot.add_cog(clickerCog(bot))
