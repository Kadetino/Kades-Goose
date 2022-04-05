import discord  # Discord API wrapper
from discord.ext import commands  # Discord BOT
import sqlite3 as sl  # SQLite database

import config  # Global settings


class EU4IdeasModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.cooldown(1, config.cd_commands, commands.BucketType.guild)
    @commands.guild_only()
    async def findIdeas(self, ctx: commands.Context, search_object: str):
        # Init
        con_ideas = sl.connect('Goose.db')  # Database connection

        # SQL Query based on input
        if "_ideas" in search_object:  # Full name - like in code
            sql_query = f"SELECT * FROM EU4IDEAS WHERE Name LIKE '{search_object.strip()}'"
            data = con_ideas.execute(sql_query).fetchone()
        elif len(search_object) == 3:  # Tag search (in situations where tag is 3 letters)
            sql_query = f"SELECT * FROM EU4IDEAS WHERE Name LIKE '{search_object.strip()}_ideas'"
            data = con_ideas.execute(sql_query).fetchone()
        elif len(data := con_ideas.execute(f"SELECT * FROM EU4IDEAS WHERE Adjective LIKE '{search_object.strip()}'").fetchall())==1:
            data = data[0]  # using := is cool - 1 result
        elif len(data := con_ideas.execute(f"SELECT * FROM EU4IDEAS WHERE Adjective LIKE '{search_object.strip()}'").fetchall())>=1:
            pass  # more than 1 result
        elif len(data := con_ideas.execute(f"SELECT * FROM EU4IDEAS WHERE Country LIKE '{search_object.strip()}'").fetchall())==1:
            data = data[0]  # 1 result
        elif len(data := con_ideas.execute(f"SELECT * FROM EU4IDEAS WHERE Country LIKE '{search_object.strip()}'").fetchall())>=1:
            pass
        else:  # When everything else fails - despair
            sql_query = f"SELECT * FROM EU4IDEAS WHERE trigger LIKE 'tag = {search_object.strip()}%'"
            data = con_ideas.execute(sql_query).fetchall()

        # Working with query result
        if data is None:  # Failure - nothing was found
            con_ideas.close()
            return await ctx.reply(f"`{search_object}` ideas weren't found.")
        elif not isinstance(data, tuple):  # fetchall() returns a list == fetchone didn't go off
            if len(data) == 1:  # 1 result = convert to tuple and all is good
                data = data[0]
            elif len(data) == 0:  # Failure - nothing was found
                con_ideas.close()
                return await ctx.reply(f"`{search_object}` ideas weren't found.")
            else:  # check if more than 1 entry was found - if 1 then it's fine
                # Making Discord embed listing all entries that suit the search
                idea_embed = discord.Embed(title="Multiple ideas found", color=discord.Colour.gold(), description=f"Try something like: `{config.prefix}findIdeas {data[0][1]}`")
                for result in data:
                    field_name = result[1]  # code name
                    ideas_name = result[12] + " Ideas"  # adjective name
                    idea_embed.add_field(name=f"`{field_name}`", value=ideas_name, inline=False)
                con_ideas.close()
                return await ctx.reply(embed=idea_embed)

        # One entry was found
        ideas_name = data[1]  # name in code
        ideas_adj = data[12] + " Ideas"  # actual Name
        traditions = data[2].replace("&&", "\n")  # traditions: first 2 modifiers at start
        ambition = data[3].replace("&&", "\n")  # final modifier after getting 7 ideas
        trigger = data[4].replace("tag =", "is").replace("TAG =", "is").replace(" && is ", "\nor\nis ")  # reason for getting set of ideas
        trigger = trigger.replace(" &&", "\n").replace("has_country_flag = ", "or\nhas flag: ")

        idea_storage = []  # all 7 ideas
        for n_idea in range(5, 12):
            if data[n_idea][-1]==" " and data[n_idea][-2]=="=":
                idea_storage.append((data[n_idea][:data[n_idea].find("=") - 1:], "Link to other same-name idea, where modifier is present. Thanks PDX."))
            else:
                idea_storage.append((data[n_idea][:data[n_idea].find("=") - 1:], data[n_idea][data[n_idea].find("=") + 1::].replace("&&", "\n")))

        # Making Discord embed
        idea_embed = discord.Embed(title=ideas_adj, color=discord.Colour.gold())  # Name
        idea_embed.add_field(name="`Trigger:`", value=trigger, inline=False)  # Trigger
        idea_embed.add_field(name="`Code:`", value=ideas_name, inline=False)  # Code name
        idea_embed.add_field(name="`Traditions:`", value=traditions, inline=False)  # Traditions
        for n_idea in range(len(idea_storage)):  # 7 ideas
            idea_embed.add_field(name=f'`#{n_idea+1}` {idea_storage[n_idea][0]}', value=idea_storage[n_idea][1], inline=False)
        idea_embed.add_field(name="`Ambition:`", value=ambition, inline=False)  # Ambition

        con_ideas.close()
        return await ctx.reply(embed=idea_embed)


def setup(bot):
    bot.add_cog(EU4IdeasModule(bot))
