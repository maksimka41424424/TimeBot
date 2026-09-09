import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

VOICE_CHANNEL_ID = 1456040423926661296

@bot.event
async def on_ready():
    # Регистрируем слэш-команды в Discord при запуске
    try:
        synced = await bot.tree.sync()
        print(f"Успешно синхронизировано слэш-команд: {len(synced)}")
    except Exception as e:
        print(f"Ошибка синхронизации слэш-команд: {e}")

    print(f"Бот {bot.user} запущен!")
    
    # Подключаемся к голосовому каналу
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel and not bot.voice_clients:
        try:
            await channel.connect()
            print(f"Подключился к: {channel.name}")
        except Exception as e:
            print(f"Ошибка подключения: {e}")

# Слэш-команда /join
@bot.tree.command(name="join", description="Вернуть бота в голосовой канал")
async def join(interaction: discord.Interaction):
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel:
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.response.send_message("Вернулся в голосовой канал! 👋")
    else:
        await interaction.response.send_message("Ошибка: голосовой канал не найден.", ephemeral=True)

token = os.getenv("BOT_TOKEN")
if token:
    bot.run(token)
