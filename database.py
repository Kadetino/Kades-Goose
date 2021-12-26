import pandas as pd
import discord

df = pd.read_csv('CSV bits\\events.csv', sep=";")


def find_event(image_output, ctx):
    for event_index in range(len(df.index)):
        if df['Name of the event'][event_index].lower() in image_output.lower():
            # Event data
            event_name = str(df['Name of the event'][event_index])
            event_condition = str(df['Conditions'][event_index])
            event_mtth = str(df['MTTH or IE'][event_index])
            event_ie = str(df['IE or MTTH'][event_index])
            event_choice = str(df['Choices'][event_index])

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
