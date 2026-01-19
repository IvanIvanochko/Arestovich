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
  - `voice_connections` - Dictionary tracking active voice connections per guild

- **`events.py`** - Discord event handlers
  - `on_ready(bot)` - Bot initialization and auto-join logic
  - `on_voice_state_update(member, before, after)` - Detects server mutes and triggers auto-unmute

### Configuration Files

- **`requirements.txt`** - Python dependencies
- **`runtime.txt`** - Python version specification
- **`.env`** - Environment variables (not in repo, create locally):
  ```
  DISCORD_TOKEN=your_bot_token
  MONITORED_ROLE_ID=your_role_id
  VOICE_CHANNEL_ID=your_channel_id (optional)
  ```

# Features

## Commands

- `!join-channel <channel_id>` - Join a voice channel by ID (admin only)
- `!leave-channel` - Leave the current voice channel (admin only)