import asyncio
import discord
from discord.ext import commands
from config import MONITORED_ROLE_ID, VOICE_CHANNEL_ID
from utils import has_role, find_recent_mute_actor
from voice_commands import voice_connections


# Щоб не запускати кілька таймерів на одну людину
pending_unmutes: dict[int, asyncio.Task] = {}


async def on_ready(bot: commands.Bot):
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    print(f"Monitored role id: {MONITORED_ROLE_ID}")
    
    # Auto-join the specific voice channel
    if VOICE_CHANNEL_ID != 0:
        channel = bot.get_channel(VOICE_CHANNEL_ID)
        if channel and isinstance(channel, discord.VoiceChannel):
            try:
                for guild_id, vc in list(voice_connections.items()):
                    if vc and not vc.is_closed():
                        await vc.disconnect()
                        voice_connections.pop(guild_id, None)
                
                vc = await channel.connect()
                voice_connections[channel.guild.id] = vc
                print(f"[BOT] Joined voice channel: {channel.name}")
            except Exception as e:
                print(f"[BOT] Failed to join voice channel: {e}")
        else:
            print(f"[BOT] Voice channel {VOICE_CHANNEL_ID} not found or is not a voice channel")


async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
):
    # Діагностика всіх voice-змін
    print(
        f"[VOICE] {member} | "
        f"channel: {getattr(before.channel, 'name', None)} -> {getattr(after.channel, 'name', None)} | "
        f"mute: {before.mute} -> {after.mute} | "
        f"self_mute: {before.self_mute} -> {after.self_mute} | "
        f"deaf: {before.deaf} -> {after.deaf} | "
        f"self_deaf: {before.self_deaf} -> {after.self_deaf}"
    )

    became_server_muted = (before.mute is False) and (after.mute is True)
    if not became_server_muted:
        return

    # Якщо людина не в voice-каналі — нічого робити
    if after.channel is None:
        return

    print("[HIT] Detected SERVER mute change -> trying audit log...")

    guild = member.guild

    # Audit log часто з'являється із затримкою
    await asyncio.sleep(1.0)

    actor = await find_recent_mute_actor(guild, member)
    print("[AUDIT] actor:", actor)

    if actor is None:
        print("[AUDIT] No actor found (maybe missing View Audit Log or too fast).")
        return

    actor_member = guild.get_member(actor.id)
    print("[AUDIT] actor_member:", actor_member)

    if actor_member is None:
        print("[AUDIT] Actor is not a guild member (integration?)")
        return

    print("[AUDIT] actor roles:", [r.id for r in actor_member.roles])
    print("[AUDIT] monitored role id:", MONITORED_ROLE_ID)

    if not has_role(actor_member, MONITORED_ROLE_ID):
        print("[AUDIT] Actor does NOT have monitored role -> skip")
        return

    # Якщо вже заплановано — не дублюємо
    if member.id in pending_unmutes and not pending_unmutes[member.id].done():
        print("[SCHEDULE] Already scheduled for this user -> skip")
        return

    print("[SCHEDULE] Will unmute in 5s:", member)

    async def unmute_later():
        try:
            print("[TASK] Sleeping 5s for:", member)
            await asyncio.sleep(5)

            current = guild.get_member(member.id)
            if current is None or current.voice is None:
                print("[TASK] User not in voice anymore -> skip")
                return

            print("[TASK] Before unmute, current.voice.mute =", current.voice.mute)
            if current.voice.mute is False:
                print("[TASK] Already unmuted -> skip")
                return

            await current.edit(mute=False, reason="Auto-unmute after 60s (monitored role action)")
            print("[TASK] Unmuted OK:", current)

        except discord.Forbidden:
            print("[TASK] Forbidden: bot lacks permission or role is too low.")
        except discord.HTTPException as e:
            print("[TASK] HTTPException:", e)
        finally:
            pending_unmutes.pop(member.id, None)

    pending_unmutes[member.id] = asyncio.create_task(unmute_later())
