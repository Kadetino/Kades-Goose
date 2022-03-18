import discord
import sqlite3 as sl

con = sl.connect('Goose.db')

def find_event(image_output, ctx):
    with con:
        sql_query=f'SELECT * FROM EU4EVENTS WHERE trim(event_name) LIKE "{image_output.strip()}"'
        data = con.execute(sql_query).fetchall()
        if len(data)!=0:
            # Event data
            event_name = str(data[0][1])
            event_condition = str(data[0][2])
            event_mtth = str(data[0][3])
            event_ie = str(data[0][4])
            event_choice = str(data[0][5])

            # Making it readable
            event_choice = event_choice.replace("&&&&Option", "\n*Option")
            event_choice = event_choice.replace("\n*Option", "Option", 1)
            stars = ["*****", "****", "***", "**", "*"]
            for star in stars:
                event_condition = event_condition.replace(star, "\n")
                event_mtth = event_mtth.replace(star, "\n")
                event_ie = event_ie.replace(star, "\n")
                event_choice = event_choice.replace(star, "\n")

            # Making Discord embed
            event_embed = discord.Embed(title=event_name, color=0x19ffe3)
            event_embed.add_field(name="Trigger", value=event_condition, inline=False)
            event_embed.add_field(name="Mean time to happen", value=event_mtth, inline=False)
            event_embed.add_field(name="Immediate effects", value=event_ie, inline=False)
            event_embed.add_field(name="Options", value=event_choice, inline=False)
            event_embed.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)

            return event_name, event_embed
        return False


def log_event_name(event_name):
    with open("searchEventLog.txt", "a") as eventLog:
        eventLog.write(event_name + "\n")