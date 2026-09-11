import os
import asyncio
import time
import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID твоих каналов
VOICE_CHANNEL_ID = 1456040423926661296
TEXT_CHANNEL_ID = 1456038468386947247

kick_lock = asyncio.Lock()
last_kick_time = 0
is_kicked_by_user = False

async def ensure_voice_connection():
    """Гарантированное удержание бота в голосовом канале 24/7"""
    global is_kicked_by_user
    
    # Если бот выходил/был кикнут — автозаход ЖЕСТКО заблокирован
    if is_kicked_by_user:
        return

    try:
        channel = bot.get_channel(VOICE_CHANNEL_ID) or await bot.fetch_channel(VOICE_CHANNEL_ID)
        if channel:
            if not channel.guild.voice_client or not channel.guild.voice_client.is_connected():
                for vc in bot.voice_clients:
                    if vc.guild.id == channel.guild.id:
                        await vc.disconnect(force=True)
                
                await channel.connect(reconnect=True, timeout=60.0, self_deaf=True)
                print(f"Канал {channel.name} зафиксирован.")
    except Exception as e:
        print(f"Ошибка удержания канала: {e}")

@tasks.loop(seconds=15)
async def keep_alive_loop():
    await ensure_voice_connection()

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано слэш-команд: {len(synced)}")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")

    print(f"Бот {bot.user} успешно запущен!")
    await ensure_voice_connection()
    
    if not keep_alive_loop.is_running():
        keep_alive_loop.start()

@bot.event
async def on_voice_state_update(member, before, after):
    global last_kick_time, is_kicked_by_user
    
    # Реакция только при отключении нашего бота из голосового канала
    if member == bot.user and before.channel is not None and after.channel is None:
        async with kick_lock:
            now_ts = time.time()
            if now_ts - last_kick_time < 3:
                return
            last_kick_time = now_ts

            # НАМЕРТВО блокируем переподключение при ЛЮБОМ выходе из канала
            is_kicked_by_user = True

            guild = before.channel.guild
            if guild.voice_client:
                try:
                    await guild.voice_client.disconnect(force=True)
                except Exception:
                    pass

            kicker_name = None

            # 5 попыток найти запись в аудите (по 1 сек задержки)
            for _ in range(5):
                await asyncio.sleep(1.0)
                if guild.me.guild_permissions.view_audit_log:
                    try:
                        async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_disconnect):
                            now = discord.utils.utcnow()
                            time_diff = abs((now - entry.created_at).total_seconds())
                            
                            # Расширенное окно до 60 секунд, чтобы поймать любые задержки Discord
                            if time_diff <= 60:
                                kicker_name = entry.user.global_name or entry.user.name
                                break
                    except Exception as e:
                        print(f"Ошибка чтения аудита: {e}")

                if kicker_name:
                    break

            target_channel = bot.get_channel(TEXT_CHANNEL_ID) or await bot.fetch_channel(TEXT_CHANNEL_ID)

            if target_channel:
                if kicker_name:
                    await target_channel.send(f"I got kicked by {kicker_name}")
                else:
                    await target_channel.send("I got disconnected")

@bot.event
async def on_message_delete(message):
    if message.author == bot.user and message.channel.id == TEXT_CHANNEL_ID:
        header = "⚠️ **Сообщение нельзя удалить!**\n"
        
        if message.content.startswith(header):
            content_to_send = message.content
        else:
            content_to_send = f"{header}{message.content}"
            
        await message.channel.send(content_to_send)

@bot.tree.command(name="join", description="Вернуть бота в голосовой канал")
async def join(interaction: discord.Interaction):
    global is_kicked_by_user
    await interaction.response.defer()
    
    try:
        is_kicked_by_user = False  # Снимаем блокировку исключительно по этой команде
        await ensure_voice_connection()
        await interaction.followup.send("Вернулся в голосовой канал! 👋")
    except Exception as e:
        await interaction.followup.send(f"Не удалось зайти в канал: {e}")

token = os.getenv("BOT_TOKEN")
if token:
    bot.run(token)
