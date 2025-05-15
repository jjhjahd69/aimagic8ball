import discord
from discord.ext import commands
from mistralai import Mistral
import asyncio
import logging
from config import *

intents = discord.Intents.default()
intents.message_content = True

client = Mistral(api_key=API_TOKEN_MISTRAL)

# базова конфігурація логера
logging.basicConfig(
    filename='magicball.log',
    filemode='a',
    level=logging.INFO,  # можна змінити на INFO, WARNING тощо
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def questionfunc(text):
    completion = client.chat.complete(
    model=model,
    messages=[
        {
            "role": "system",
            "content": prompt

        },
        {
            "role": "user",
            "content": f"{text}"
        }
    ],
    max_tokens=40,
    temperature=0.9
    )

    return completion.choices[0].message.content

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.tree.command(name='запитати', description='Поставити запитання магічній кулі')
@discord.app_commands.describe(question="Текст вашого запитання")
async def ask_magic_ball(interaction: discord.Interaction, question: discord.app_commands.Range[str, 1, 50]):
    await interaction.response.defer()

    animation_frames = [
        "🔮 Магічна куля думає.",
        "🔮 Магічна куля думає..",
        "🔮 Магічна куля думає...",
    ]

    for frame in animation_frames:
        await interaction.edit_original_response(content=frame)
        await asyncio.sleep(0.1)  # пауза між кадрами

    try:
        response = await asyncio.to_thread(questionfunc, question)

        if response == question:
            raise Exception
    except Exception as e:
        print(e)
        await interaction.edit_original_response(content=f"На жаль, на зараз духи не виходять на зв'язок :(")
        logging.error(f"Магічна куля не дала відповіді. Питання: {question}")
        return

    logging.info(f"!!!! Хтось звернувся до магічної кулі. Питання: {question}, відповідь: {response}")
    await interaction.edit_original_response(content=f"**{question}**\n🔮 Магічна куля відповідає: `{response}`"
    )

@bot.event
async def on_ready():
    print(f'Магічна куля працює! {bot.user}')
    activity = discord.Game(name="Магічно блимає")
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await bot.tree.sync()


bot.run(TOKEN)
