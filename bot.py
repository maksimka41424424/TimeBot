import os
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

VOICE_CHANNEL_ID = 1456040423926661296

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Успешно синхронизировано слэш-команд: {len(synced)}")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")

    print(f"Бот {bot.user} запущен!")
    
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel and not bot.voice_clients:
        try:
            await channel.connect()
            print(f"Подключился к: {channel.name}")
        except Exception as e:
            print(f"Ошибка подключения: {e}")

# Отслеживаем отключение из голосового канала
@bot.event
async def on_voice_state_update(member, before, after):
    # Проверяем, что отключили именно нашего бота
    if member == bot.user and before.channel is not None and after.channel is None:
        guild = before.channel.guild
        kicker_name = "someone"
        
        # Небольшая пауза, чтобы Discord успел записать событие в журнал аудита
        await asyncio.sleep(0.5)
        
        try:
            # Ищем последнюю запись об отключении пользователя из голосового канала
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect):
                if entry.target == bot.user:
                    kicker_name = entry.user.global_name or entry.user.name
                    break
        except Exception as e:
            print(f"Не удалось прочитать журнал аудита: {e}")

        # Находим текстовый канал для отправки сообщения (системный или первый доступный)
        target_text_channel = guild.system_channel
        if not target_text_channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    target_text_channel = ch
                    break

        if target_text_channel:
            await target_text_channel.send(f"I got kicked by {kicker_name}")

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
