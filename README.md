# Core Files

- **`bot.py`** - Main entry point
  - Initializes the Discord bot with intents
  - Registers commands and event handlers
  - Contains command decorators that delegate to other modules

- **`config.py`** - Configuration management
  - Loads environment variables from `.env` file
  - Exports `TOKEN`, `MONITORED_ROLE_ID`, `VOICE_CHANNEL_ID`

- **`utils.py`** - Utility helper functions
  - `has_role(member, role_id)` - Check if a member has a specific role
  - `find_recent_mute_actor(guild, target, window_sec)` - Search audit logs to find who muted a user

- **`voice_commands.py`** - Voice channel operations
  - `join_voice(ctx, bot, channel_id)` - Join a voice channel by ID
  - `leave_voice(ctx)` - Leave the current voice channel
  - `play_join(ctx, filename)` - Play audio in connected voice channel
  - `voice_connections` - Dictionary tracking active voice connections per guild

- **`events.py`** - Discord event handlers
  - `on_ready(bot)` - Bot initialization and auto-join logic
  - `on_voice_state_update(member, before, after)` - Detects server mutes, triggers auto-unmute, and plays join audio

- **`greetings.py`** - Per-member audio greeting system
  - Scans `Molda Voice/` for `*_Molda.(mp3|opus)` files
  - Maps member IDs to greeting files via environment tokens
  - Registers dynamic `!play-audio-greeting-<name>` commands

- **`audio_encoder.py`** - Audio encoding utilities
  - Converts MP3 to Opus format for lower memory usage
  - `encode_all_mp3s()` - Batch encode all MP3 files
  - `encode_mp3_to_opus()` - Encode a single file

- **`ffmpeg_helper.py`** - FFmpeg binary management
  - Locates or downloads FFmpeg for audio playback

### Configuration Files

- **`requirements.txt`** - Python dependencies
- **`runtime.txt`** - Python version specification
- **`.env`** - Environment variables (not in repo, create locally):
  ```
  DISCORD_TOKEN=your_bot_token
  MONITORED_ROLE_ID=your_role_id
  VOICE_CHANNEL_ID=your_channel_id (optional)
  JOIN_PLAY_DELAY=1.0 (seconds to wait after join before playing audio; default 1.0)
  
  # Per-member greeting tokens (map member ID to greeting file)
  # For a file named Ivan_Molda.mp3, use either IVAN or Ivan
  IVAN=123456789012345678
  ALEX=123456789012345679
  ```

# Features

## Audio Greetings

When a user joins a voice channel where the bot is connected:
- The bot automatically plays a join audio file after a short delay (`JOIN_PLAY_DELAY`)
- If the member has a token mapping (e.g., `IVAN=<member_id>`), their specific greeting plays (e.g., `Ivan_Molda.mp3`)
- Otherwise, the default `New_comers_molda.mp3` plays

## Commands

- `!join-channel <channel_id>` - Join a voice channel by ID (admin only)
- `!leave-channel` - Leave the current voice channel (admin only)
- `!play-join [filename]` - Play configured join audio or optional filename (admin only)
- `!play-audio-greeting-<name>` - Play a specific member's greeting audio (admin only, dynamically registered)
- `!encode-audio` - Pre-encode all MP3 files to Opus format (admin only)