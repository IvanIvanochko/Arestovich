import asyncio
import os
import discord
from discord.ext import commands, tasks
from pathlib import Path

from config import MONITORED_ROLE_ID, VOICE_CHANNEL_ID, JOIN_PLAY_DELAY, MOLDA_CHANNEL_ID, MOLDA_REJOIN_INTERVAL
from utils import has_role, find_recent_mute_actor
from voice_commands import voice_connections
from ffmpeg_helper import get_ffmpeg_exec
from greetings import get_greeting_for_member

# Resolve ffmpeg executable for event playback
FFMPEG_EXEC = get_ffmpeg_exec()
if not FFMPEG_EXEC:
    print("[FFMPEG] ffmpeg executable not found. Set FFMPEG_PATH env var or ensure ffmpeg is available.")

# Path to the join audio file (relative to project)
JOIN_AUDIO = Path(__file__).resolve().parent / "Molda Voice" / "New_comers_molda.mp3"
if not JOIN_AUDIO.exists():
    print(f"[AUDIO] Join audio not found at: {JOIN_AUDIO}")


# Щоб не запускати кілька таймерів на одну людину
pending_unmutes: dict[int, asyncio.Task] = {}

# Molda channel auto-rejoin state tracking
# Maps guild_id to the target molda channel_id (0 means auto-rejoin disabled)
molda_rejoin_targets: dict[int, int] = {}
# Maps guild_id to the hourly rejoin task
molda_rejoin_tasks: dict[int, asyncio.Task] = {}


async def on_ready(bot: commands.Bot):
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    print(f"Monitored role id: {MONITORED_ROLE_ID}")
    
    # Auto-join the specific voice channel
    if VOICE_CHANNEL_ID != 0:
        channel = bot.get_channel(VOICE_CHANNEL_ID)
        if channel and isinstance(channel, discord.VoiceChannel):
            try:
                for guild_id, vc in list(voice_connections.items()):
                    # VoiceClient may not have is_closed(); check connection by channel
                    if vc and getattr(vc, "channel", None) is not None:
                        await vc.disconnect()
                        voice_connections.pop(guild_id, None)
                
                vc = await channel.connect()
                voice_connections[channel.guild.id] = vc
                print(f"[BOT] Joined voice channel: {channel.name}")
            except Exception as e:
                print(f"[BOT] Failed to join voice channel: {e}")
        else:
            print(f"[BOT] Voice channel {VOICE_CHANNEL_ID} not found or is not a voice channel")
    
    # Auto-join molda channel if configured (with retry logic)
    # NOTE: If MOLDA_CHANNEL_ID fails consistently, the channel may have Discord API issues
    # Use !join-channel-molda command instead to manually attempt connection
    # Disabled auto-join on startup to avoid spamming retries
    # if MOLDA_CHANNEL_ID != 0:
    #     await _attempt_molda_connect(bot, MOLDA_CHANNEL_ID, retry_count=3)


async def _attempt_molda_connect(bot: commands.Bot, channel_id: int, retry_count: int = 3):
    """Attempt to connect to molda channel with retry logic."""
    channel = bot.get_channel(channel_id)
    if not channel or not isinstance(channel, discord.VoiceChannel):
        print(f"[MOLDA] Channel {channel_id} not found or not a voice channel")
        return False
    
    guild_id = channel.guild.id
    
    # Check bot permissions
    perms = channel.permissions_for(channel.guild.me)
    if not perms.connect:
        print(f"[MOLDA] Bot lacks CONNECT permission for channel {channel.name}")
        return False
    
    # Disconnect from any existing connection in this guild
    if guild_id in voice_connections and voice_connections[guild_id]:
        try:
            await voice_connections[guild_id].disconnect()
        except Exception as e:
            print(f"[MOLDA] Error disconnecting existing voice connection: {e}")
        voice_connections.pop(guild_id, None)
    
    # Retry with exponential backoff
    for attempt in range(retry_count):
        try:
            print(f"[MOLDA] Connecting attempt {attempt + 1}/{retry_count} to {channel.name} (ID: {channel_id})...")
            await asyncio.sleep(0.5 + (attempt * 1.0))  # Exponential backoff: 0.5s, 1.5s, 2.5s
            
            vc = await asyncio.wait_for(channel.connect(), timeout=15.0)
            voice_connections[guild_id] = vc
            molda_rejoin_targets[guild_id] = channel_id
            print(f"[MOLDA] ✅ Successfully joined voice channel: {channel.name}")
            
            # Start hourly rejoin task if not already running
            if guild_id not in molda_rejoin_tasks or molda_rejoin_tasks[guild_id].done():
                molda_rejoin_tasks[guild_id] = asyncio.create_task(
                    _molda_hourly_rejoin_loop(bot, guild_id, channel_id)
                )
            return True
            
        except asyncio.TimeoutError:
            print(f"[MOLDA] Attempt {attempt + 1}/{retry_count}: Connection timed out (network/server delay)")
            if attempt == retry_count - 1:
                print(f"[MOLDA] ❌ All {retry_count} connection attempts failed - timeout. Channel may be experiencing connectivity issues.")
        except IndexError as e:
            print(f"[MOLDA] Attempt {attempt + 1}/{retry_count}: Encryption mode selection failed (Discord API issue)")
            if attempt == retry_count - 1:
                print(f"[MOLDA] ❌ All {retry_count} attempts failed - Discord is not providing encryption modes for this channel.")
                print(f"[MOLDA] This is a Discord server configuration issue. The channel cannot be used with bot voice connections.")
                print(f"[MOLDA] Recommended actions:")
                print(f"[MOLDA]   1. Try joining a different voice channel")
                print(f"[MOLDA]   2. Check if this channel has special Discord settings or permissions")
                print(f"[MOLDA]   3. Contact your server administrator about the channel configuration")
        except discord.Forbidden:
            print(f"[MOLDA] ❌ Forbidden - bot lacks permissions to join {channel.name}")
            return False
        except discord.HTTPException as e:
            print(f"[MOLDA] Attempt {attempt + 1}/{retry_count}: HTTP error - {e}")
            if attempt == retry_count - 1:
                print(f"[MOLDA] ❌ All {retry_count} attempts failed - HTTP connection error")
        except Exception as e:
            print(f"[MOLDA] Attempt {attempt + 1}/{retry_count}: {type(e).__name__}: {e}")
            if attempt == retry_count - 1:
                print(f"[MOLDA] ❌ All {retry_count} attempts failed")
    
    return False


async def _molda_hourly_rejoin_loop(bot: commands.Bot, guild_id: int, channel_id: int):
    """Rejoin the molda channel every hour."""
    while True:
        try:
            await asyncio.sleep(MOLDA_REJOIN_INTERVAL)
            
            # Check if auto-rejoin is still enabled for this guild
            if molda_rejoin_targets.get(guild_id) != channel_id:
                print(f"[MOLDA] Auto-rejoin disabled for guild {guild_id}")
                break
            
            channel = bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                print(f"[MOLDA] Channel {channel_id} not found or not a voice channel")
                break
            
            vc = voice_connections.get(guild_id)
            if not vc or getattr(vc, "channel", None) is None:
                # Bot is not in a channel, try to rejoin with retry
                print(f"[MOLDA] Hourly rejoin: Bot not in channel, attempting to rejoin...")
                await _attempt_molda_connect(bot, channel_id, retry_count=2)
            else:
                # Bot is in a channel, verify it's the correct one
                if vc.channel.id != channel_id:
                    # Bot is in wrong channel, move back
                    try:
                        await vc.move_to(channel)
                        print(f"[MOLDA] Hourly check: Moved back to correct molda channel")
                    except Exception as e:
                        print(f"[MOLDA] Failed to move back during hourly check: {type(e).__name__}: {e}")
                else:
                    print(f"[MOLDA] Hourly check: Still in correct molda channel")
                    
        except asyncio.CancelledError:
            print(f"[MOLDA] Rejoin loop for guild {guild_id} cancelled")
            break
        except Exception as e:
            print(f"[MOLDA] Error in hourly rejoin loop: {type(e).__name__}: {e}")


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

    # Guild reference (used by join-audio logic and audit checks)
    guild = member.guild
    guild_id = guild.id
    
    # Handle bot disconnect/move detection for molda channel auto-rejoin
    if member.bot and member.id == guild.me.id:
        target_molda_id = molda_rejoin_targets.get(guild_id)
        if target_molda_id:
            # Bot was disconnected from molda channel
            if before.channel and before.channel.id == target_molda_id and after.channel is None:
                print(f"[MOLDA] Bot disconnected from molda channel, rejoining...")
                try:
                    channel = guild.get_channel(target_molda_id)
                    if channel and isinstance(channel, discord.VoiceChannel):
                        # Check permissions
                        perms = channel.permissions_for(guild.me)
                        if not perms.connect:
                            print(f"[MOLDA] Cannot rejoin - bot lacks CONNECT permission")
                            return
                        
                        vc = await channel.connect()
                        voice_connections[guild_id] = vc
                        print(f"[MOLDA] Rejoined molda channel after disconnect: {channel.name}")
                except asyncio.TimeoutError:
                    print(f"[MOLDA] Timeout rejoining after disconnect")
                except IndexError:
                    print(f"[MOLDA] Voice handshake failed - encryption mode not provided")
                except discord.Forbidden:
                    print(f"[MOLDA] Forbidden - bot lacks permissions")
                except Exception as e:
                    print(f"[MOLDA] Failed to rejoin after disconnect: {type(e).__name__}: {e}")
            
            # Bot was moved to a different channel
            elif before.channel and after.channel and before.channel.id == target_molda_id and after.channel.id != target_molda_id:
                print(f"[MOLDA] Bot moved away from molda channel, moving back...")
                try:
                    channel = guild.get_channel(target_molda_id)
                    if channel and isinstance(channel, discord.VoiceChannel):
                        vc = voice_connections.get(guild_id)
                        if vc:
                            await vc.move_to(channel)
                            print(f"[MOLDA] Moved back to molda channel: {channel.name}")
                except Exception as e:
                    print(f"[MOLDA] Failed to move back to molda channel: {type(e).__name__}: {e}")

    # Play join audio when a non-bot user enters a channel where the bot is connected
    try:
        joined = (before.channel is None) and (after.channel is not None)
        if joined and not member.bot:
            guild_id = after.channel.guild.id
            vc = voice_connections.get(guild_id)
            # Check active connection by channel presence
            if vc and getattr(vc, "channel", None) is not None and vc.channel.id == after.channel.id:
                # Wait a short configurable delay to allow the user to fully connect
                try:
                    await asyncio.sleep(JOIN_PLAY_DELAY)
                except Exception:
                    pass
                # Re-fetch member from guild and verify they're still in the same channel
                current_member = guild.get_member(member.id)
                if current_member is None or current_member.voice is None or current_member.voice.channel is None:
                    print(f"[AUDIO] Member {member} left or not fully connected after delay; skipping playback.")
                    return
                if current_member.voice.channel.id != after.channel.id:
                    print(f"[AUDIO] Member {member} moved channels after delay; skipping playback.")
                    return
                # If a specific greeting token exists for this member, use it
                greeting_filename = get_greeting_for_member(member.id)
                print(f"[AUDIO] Checking greeting for member {member.id} ({member.name}): {greeting_filename}")
                if greeting_filename:
                    audio_path = Path(__file__).resolve().parent / "Molda Voice" / greeting_filename
                    # Try .opus version first
                    opus_path = audio_path.with_suffix('.opus')
                    if opus_path.exists():
                        audio_path = opus_path
                else:
                    audio_path = JOIN_AUDIO
                    # Try .opus version first
                    opus_audio = JOIN_AUDIO.with_suffix('.opus')
                    if opus_audio.exists():
                        audio_path = opus_audio

                if audio_path.exists():
                    try:
                        # stop current audio if playing
                        if vc.is_playing():
                            vc.stop()
                        if FFMPEG_EXEC is None:
                            print("[AUDIO] ffmpeg not available; cannot play audio.")
                        else:
                            try:
                                source = await discord.FFmpegOpusAudio.from_probe(str(audio_path), executable=FFMPEG_EXEC)
                                vc.play(source)
                                print(f"[AUDIO] Played join audio for {member} in {after.channel.name}")
                            except Exception as e:
                                print("[AUDIO] Failed to play join audio:", e)
                    except Exception as e:
                        print("[AUDIO] Failed to play join audio:", e)
                else:
                    print(f"[AUDIO] Audio file not present; skipping playback. ({audio_path})")
    except Exception as e:
        print("[AUDIO] Error during join-audio handling:", e)

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
