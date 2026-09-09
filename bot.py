import os
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID твоих каналов
VOICE_CHANNEL_ID = 1456040423926661296
TEXT_CHANNEL_ID = 1234567890123456789  # <--- ВСТАВЬ СЮДА ID СВОЕГО ТЕКСТОВОГО ЧАТА

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано слэш-команд: {len(synced)}")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")

    print(f"Бот {bot.user} запущен!")
    
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel and not bot.voice_clients:
        try:
            await channel.connect()
            print(f"Подключился к ГС: {channel.name}")
        except Exception as e:
            print(f"Ошибка подключения: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    # Проверяем, что отключили именно нашего бота
    if member == bot.user and before.channel is not None and after.channel is None:
        guild = before.channel.guild
        kicker_name = None
        
        # Задержка 1 секунда, чтобы Discord успел записать событие
        await asyncio.sleep(1)
        
        try:
            # Берем самое последнее запись отключения из голосового канала
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                # Сравниваем время записи с текущим временем
                now = discord.utils.utcnow()
                time_diff = (now - entry.created_at).total_seconds()
                
                # Если запись создана менее 5 секунд назад — это имя того, кто кикнул
                if time_diff < 5:
                    kicker_name = entry.user.global_name or entry.user.name
                    break
        except discord.Forbidden:
            print("❌ Ошибка: Включи право 'Просмотр журнала аудита' у роли бота!")
        except Exception as e:
            print(f"Ошибка аудита: {e}")

        text_channel = bot.get_channel(TEXT_CHANNEL_ID)
        if text_channel:
            if kicker_name:
                await text_channel.send(f"I got kicked by {kicker_name}")
            else:
                await text_channel.send("I got disconnected")

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
