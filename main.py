import discord
from discord.ext import commands
import asyncio
import aiohttp
import logging
from config import *
from collections import defaultdict
from datetime import datetime, timedelta

user_timestamps = defaultdict(list)
LIMIT = 2  # максимум запитів
WINDOW = timedelta(minutes=1)

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

async def animate_thinking(interaction, stop_event: asyncio.Event):
    while not stop_event.is_set():
        for frame in animation_frames:
            if stop_event.is_set():
                return
            await interaction.edit_original_response(content=frame)
            await asyncio.sleep(0.6)


@bot.tree.command(name='запитати', description='Поставити запитання магічній кулі')
@discord.app_commands.describe(question="Текст вашого запитання")
async def ask_magic_ball(interaction: discord.Interaction, question: discord.app_commands.Range[str, 1, 100]):
    user_id = interaction.user.id
    now = datetime.utcnow()

    # очищаємо старі запити
    user_timestamps[user_id] = [
        t for t in user_timestamps[user_id] if now - t < WINDOW
    ]

    if len(user_timestamps[user_id]) >= LIMIT:
        await interaction.response.send_message("Магічна куля перевантажена твоїми запитами! Їй треба охолодитись.", ephemeral=True)
        return

    user_timestamps[user_id].append(now)

    await interaction.response.defer()

    stop_event = asyncio.Event()
    animation_task = asyncio.create_task(animate_thinking(interaction, stop_event))

    try:
        response = await asyncio.wait_for(questionfunc(question), timeout=20)
        if response == question:
            raise Exception

    except asyncio.TimeoutError:
        await interaction.edit_original_response(content="Ой-ой... чомусь відповідь від духів так і не надійшла...")
        logging.error(f"Таймаут відповіді. Питання: {question}")
        return

    except Exception as e:
        print(e)
        await interaction.edit_original_response(content=f"На жаль, на зараз духи не виходять на зв'язок :(")
        logging.error(f"Магічна куля не дала відповіді. Питання: {question}")
        return

    finally:
        stop_event.set()
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
