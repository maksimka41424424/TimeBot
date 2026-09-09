import os
import discord
from discord.ext import commands

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID твоего голосового канала
VOICE_CHANNEL_ID = 1456040423926661296

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен и готов к работе!")

    # Подключаемся только ОДИН раз при запуске проекта
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel:
        try:
            await channel.connect()
            print(f"Успешно подключился к голосовому каналу: {channel.name}")
        except Exception as e:
            print(f"Не удалось подключиться к ГС: {e}")
    else:
        print("❌ Голосовой канал с таким ID не найден!")

@bot.command()
async def ping(ctx):
    await ctx.send("Понг! Бот на связи.")

token = os.getenv("BOT_TOKEN")

if not token:
    print("Ошибка: Токен бота не найден!")
else:
    bot.run(token)
