# Project: discord_unmute_bot
# File: bot.py

import discord
from discord.ext import commands

from config import TOKEN, MONITORED_ROLE_ID
from voice_commands import join_voice, leave_voice, play_join
import events
from greetings import register_greeting_commands

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Register dynamic greeting commands (from `Molda Voice` files)
register_greeting_commands(bot)


@bot.command(name="join-channel")
@commands.has_permissions(administrator=True)
async def join_channel_cmd(ctx: commands.Context, channel_id: int):
    """Join a voice channel by ID. Usage: !join-channel <channel_id>"""
    await join_voice(ctx, bot, channel_id)


@bot.command(name="leave-channel")
@commands.has_permissions(administrator=True)
async def leave_channel_cmd(ctx: commands.Context):
    """Leave the current voice channel."""
    await leave_voice(ctx)


@bot.command(name="play-join")
@commands.has_permissions(administrator=True)
async def play_join_cmd(ctx: commands.Context, filename: str = None):
    """Play the configured join audio (admin only). Optionally specify filename in `Molda Voice/`."""
    await play_join(ctx, filename)


@bot.event
async def on_ready():
    await events.on_ready(bot)


@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
):
    await events.on_voice_state_update(member, before, after)


def main():
    if not TOKEN or MONITORED_ROLE_ID == 0:
        raise RuntimeError("Set DISCORD_TOKEN and MONITORED_ROLE_ID in .env")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()