import discord
import pytesseract
import io
import requests
from discord.ext import commands
from PIL import Image

import config

bot = commands.Bot(command_prefix='--')


@bot.event
async def on_ready():
    print('Logged on as {0.user}!'.format(bot))


@bot.command()
async def send_Embed(ctx, event_name="NaN - Event Name", event_description="NaN",
                     event_requirements="NaN", event_choices="NaN"):
    """Embed Для отправки ивента, найденного в базе данных"""

    embedVar = discord.Embed(title=event_name, color=0x19ffe3)
    embedVar.add_field(name="Requirements", value=event_requirements, inline=False)
    embedVar.add_field(name="Description", value=event_description, inline=False)
    embedVar.add_field(name="Event Choices", value=event_choices, inline=False)
    embedVar.set_footer(text="Requested by {0}".format(ctx.author), icon_url=ctx.author.avatar_url)
    await ctx.reply(embed=embedVar)


@bot.command(pass_context=True)
async def extract_attach(ctx):
    # Получить изображение как вложенный файл
    try:
        img_url = ctx.message.attachments[0]

    except Exception:
        await ctx.send('Error: no attached images')

    else:
        img = Image.open(io.BytesIO(await img_url.read()))

        # Обработка текста
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path
        text = pytesseract.image_to_string(img)

        await ctx.message.channel.send(text)

@bot.command(pass_context=True)
async def extract_url(ctx, *img_urls):
    # Получить изображение по ссылке
    for url in img_urls:
        try:
            response = requests.get(url)
        
        except Exception:
            current_output = ''
            if(len(img_urls)>1):
                current_output =  f"{img_urls.index(url)+1}) Error: can't recognize the photo" 
            else:
                current_output = "Error: can't recognize the photo"
            await ctx.send(current_output)

        else:
            img = Image.open(io.BytesIO(response.content))

            # Обработка текста
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path
            text = pytesseract.image_to_string(img)

            await ctx.message.channel.send(text)

# Если оставляем логирование, то лучше оформить как вложенный декоратор
'''with open('log.txt', 'at') as log_file:
    log_file.write("Message:" + ctx.message.content)
    log_file.write("\nOutput:\n" + text + "\n------------------\n")
'''


@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    await ctx.bot.logout()


bot.run(config.token)
