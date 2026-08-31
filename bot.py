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

# Команда для входа в твой голосовой канал
@bot.command()
async def join(ctx):
    # Проверяем, находится ли тот, кто написал команду, в голосовом канале
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
        
        # Если бот уже где-то сидит, сначала выходим оттуда
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
            
        await ctx.send(f"Успешно зашел в голосовой канал: **{channel.name}**!")
    else:
        await ctx.send("❌ Сначала зайди в голосовой канал, чтобы я понял, куда заходить!")

# Команда для выхода из голосового канала
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Бот вышел из голосового канала.")
    else:
        await ctx.send("Я и так не нахожусь ни в одном голосовом канале.")

# Базовая команда проверки
@bot.command()
async def ping(ctx):
    await ctx.send("Понг! Бот на связи 24/7.")

# Получение токена из переменных окружения
token = os.getenv("BOT_TOKEN")

if not token:
    print("Ошибка: Токен бота не найден!")
else:
    bot.run(token)
