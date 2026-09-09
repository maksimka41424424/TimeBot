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
TEXT_CHANNEL_ID = 1456038468386947247

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано слэш-команд: {len(synced)}")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")

    print(f"Бот {bot.user} успешно запущен!")
    
    # Автоподключение при старте
    try:
        channel = bot.get_channel(VOICE_CHANNEL_ID) or await bot.fetch_channel(VOICE_CHANNEL_ID)
        if channel:
            for vc in bot.voice_clients:
                if vc.guild.id == channel.guild.id:
                    await vc.disconnect(force=True)
            await channel.connect()
            print(f"Подключился к ГС: {channel.name}")
    except Exception as e:
        print(f"Ошибка автоподключения: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    # Если из ГС выгнали именно нашего бота
    if member == bot.user and before.channel is not None and after.channel is None:
        guild = before.channel.guild
        
        # Сбрасываем зависшее подключение
        if guild.voice_client:
            try:
                await guild.voice_client.disconnect(force=True)
            except Exception:
                pass

        kicker_name = None
        error_reason = None
        
        await asyncio.sleep(1)
        
        try:
            # Берем самую последнюю запись об отключении из ГС
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                now = discord.utils.utcnow()
                time_diff = abs((now - entry.created_at).total_seconds())
                
                # Проверяем, что событие произошло в течение последней минуты
                if time_diff < 60:
                    kicker_name = entry.user.global_name or entry.user.name
                else:
                    error_reason = f"запись в аудите устарела ({int(time_diff)} сек назад)"
        except discord.Forbidden:
            error_reason = "нет права 'View Audit Log'"
        except Exception as e:
            error_reason = f"ошибка API: {e}"

        # Отправка сообщения в указанный чат
        target_channel = None
        try:
            target_channel = bot.get_channel(TEXT_CHANNEL_ID) or await bot.fetch_channel(TEXT_CHANNEL_ID)
        except Exception:
            target_channel = guild.system_channel

        if target_channel:
            if kicker_name:
                await target_channel.send(f"I got kicked by {kicker_name}")
            else:
                msg = "I got disconnected"
                if error_reason:
                    msg += f" ({error_reason})"
                await target_channel.send(msg)

@bot.tree.command(name="join", description="Вернуть бота в голосовой канал")
async def join(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        channel = bot.get_channel(VOICE_CHANNEL_ID) or await bot.fetch_channel(VOICE_CHANNEL_ID)
        if channel:
            if interaction.guild.voice_client:
                try:
                    await interaction.guild.voice_client.disconnect(force=True)
                except Exception:
                    pass
            
            await channel.connect()
            await interaction.followup.send("Вернулся в голосовой канал! 👋")
        else:
            await interaction.followup.send("Ошибка: голосовой канал не найден.")
    except Exception as e:
        await interaction.followup.send(f"Не удалось зайти в канал: {e}")

token = os.getenv("BOT_TOKEN")
if token:
    bot.run(token)
