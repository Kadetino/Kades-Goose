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
async def extract(ctx, *img_urls):
    # Получить изображение как вложенный файл
    if(ctx.message.attachments):
        for attach in range(len(ctx.message.attachments)):
            try:
                img_url = ctx.message.attachments[attach]
            
            except Exception:
                current_output = 'Error: can\'t recognize attached file'
                if(len(ctx.message.attachments)>1):
                    current_output =  f'{attach+1}) Error: can\'t recognize attached file'
                
                await ctx.send(current_output)
            
            else:
                img = Image.open(io.BytesIO(await img_url.read()))

                # Обработка текста
                pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path
                text = "Result:\n" + pytesseract.image_to_string(img)
                if(len(ctx.message.attachments)>1):
                    text = f"{attach+1}) {text}"

                await ctx.message.channel.send(text)
    
    # Получить изображение по ссылке
    else:
        for url in range(len(img_urls)):
            try:
                response = requests.get(img_urls[url])

            except Exception:
                current_output = ''
                if(len(img_urls)>1):
                    current_output =  f"{url+1}) Error: can't recognize the URL" 
                else:
                    current_output = "Error: can't recognize the URL"
                await ctx.send(current_output)

            else:
                img = Image.open(io.BytesIO(response.content))

                # Обработка текста
                pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd_path
                text = "Result:\n" + pytesseract.image_to_string(img)
                if(len(img_urls)>1):
                    text = f"{url+1}) {text}"
                
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
