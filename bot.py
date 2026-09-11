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
    
    # Если бота кикнул человек — автозаход ЖЕСТКО заблокирован
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
    
    # Реакция только если из канала выбросило нашего бота
    if member == bot.user and before.channel is not None and after.channel is None:
        async with kick_lock:
            now_ts = time.time()
            if now_ts - last_kick_time < 3:
                return
            last_kick_time = now_ts

            # СРАЗУ блокируем фоновый автозаход, чтобы бот НЕ заходил обратно
            is_kicked_by_user = True

            guild = before.channel.guild
            kicker_name = None

            # Ждем 1.5 секунды, пока Discord запишет кик в аудит
            await asyncio.sleep(1.5)

            if guild.me.guild_permissions.view_audit_log:
                try:
                    async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect):
                        now = discord.utils.utcnow()
                        time_diff = abs((now - entry.created_at).total_seconds())
                        
                        # Берем свежую запись о кике без проверки entry.target
                        if time_diff <= 30:
                            kicker_name = entry.user.global_name or entry.user.name
                            break
                except Exception as e:
                    print(f"Ошибка аудита: {e}")

            target_channel = bot.get_channel(TEXT_CHANNEL_ID) or await bot.fetch_channel(TEXT_CHANNEL_ID)

            if kicker_name:
                # Если кикнул человек — пишем ник и ОСТАЕМСЯ СНАРУЖИ
                if target_channel:
                    await target_channel.send(f"I got kicked by {kicker_name}")
            else:
                # Если записи в аудите нет (реальный сбой сети), снимаем блок и перезаходим
                is_kicked_by_user = False
                await ensure_voice_connection()

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
        is_kicked_by_user = False  # Снимаем блокировку по команде /join
        await ensure_voice_connection()
        await interaction.followup.send("Вернулся в голосовой канал! 👋")
    except Exception as e:
        await interaction.followup.send(f"Не удалось зайти в канал: {e}")

token = os.getenv("BOT_TOKEN")
if token:
    bot.run(token)
