import discord
from discord.ext import commands


voice_connections: dict[int, discord.VoiceClient] = {}


async def join_voice(ctx: commands.Context, bot: commands.Bot, channel_id: int):
    """Join a voice channel by ID. Usage: !join-channel <channel_id>"""
    channel = bot.get_channel(channel_id)
    
    if channel is None:
        await ctx.send(f"Channel with ID {channel_id} not found!")
        return
    
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send(f"Channel {channel_id} is not a voice channel!")
        return
    
    guild_id = ctx.guild.id
    
    # Disconnect from existing connection if any
    if guild_id in voice_connections:
        await voice_connections[guild_id].disconnect()
    
    try:
        vc = await channel.connect()
        voice_connections[guild_id] = vc
        await ctx.send(f"Joined {channel.name}!")
    except Exception as e:
        await ctx.send(f"Failed to join channel: {e}")


async def leave_voice(ctx: commands.Context):
    """Leave the current voice channel."""
    guild_id = ctx.guild.id
    
    if guild_id not in voice_connections or voice_connections[guild_id] is None:
        await ctx.send("I'm not in a voice channel!")
        return
    
    await voice_connections[guild_id].disconnect()
    voice_connections.pop(guild_id, None)
    await ctx.send("Left the voice channel!")
