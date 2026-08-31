import os
import discord
from discord.ext import commands

# Настройка интентов (разрешений для бота)
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Нужно для работы в голосовых каналах

# Создаем экземпляр бота
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен и готов к работе!")

# Пример базовой команды (можешь заменить на свою логику)
@bot.command()
async def ping(ctx):
    await ctx.send("Понг! Бот на связи 24/7.")

# Получаем токен из безопасных переменных окружения (на Render или в .env дома)
token = os.getenv("BOT_TOKEN")

if not token:
    print("Ошибка: Токен бота не найден! Проверь настройки .env или переменных окружения на хостинге.")
else:
    bot.run(token)