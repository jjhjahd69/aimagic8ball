import discord
from discord.ext import commands
import asyncio
import aiohttp
import logging
from config import *

intents = discord.Intents.default()
intents.message_content = True

# базова конфігурація логера
logging.basicConfig(
    filename='magicball.log',
    filemode='a',
    level=logging.INFO,  # можна змінити на INFO, WARNING тощо
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def questionfunc(text):

    headers = {
        "Authorization": f"Bearer {API_TOKEN_MISTRAL}",
        "Content-Type": "application/json"
        }

    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
    "max_tokens": 100,
    "temperature": 0.9
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"ошибка: {resp.status}, {text}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

bot = commands.Bot(command_prefix="!", intents=intents)

animation_frames = [
    "🔮 Магічна куля думає.",
    "🔮 Магічна куля думає..",
    "🔮 Магічна куля думає...",
]

async def animate_thinking(interaction):
    while True:
        for frame in animation_frames:
            await interaction.edit_original_response(content=frame)
            await asyncio.sleep(0.2)


@bot.tree.command(name='запитати', description='Поставити запитання магічній кулі')
@discord.app_commands.describe(question="Текст вашого запитання")
async def ask_magic_ball(interaction: discord.Interaction, question: discord.app_commands.Range[str, 1, 100]):
    await interaction.response.defer()

    animation_task = asyncio.create_task(animate_thinking(interaction))

    try:
        response = await questionfunc(question)
        if response == question:
            raise Exception

    except Exception as e:
        print(e)
        await interaction.edit_original_response(content=f"На жаль, на зараз духи не виходять на зв'язок :(")
        logging.error(f"Магічна куля не дала відповіді. Питання: {question}")
        return

    finally:
        animation_task.cancel()
        try:
            await animation_task
        except asyncio.CancelledError:
            pass

    logging.info(f"!!!! {interaction.user.name} звернувся до магічної кулі на сервері {interaction.guild.name} ({interaction.guild.id}). Питання: {question}, відповідь: {response}")
    await interaction.edit_original_response(content=f"**{question}**\n🔮 Магічна куля відповідає: `{response}`"
    )

@bot.event
async def on_ready():
    print(f'Магічна куля працює! {bot.user}')
    activity = discord.Game(name="Магічно блимає")
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await bot.tree.sync()


bot.run(TOKEN)
