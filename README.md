# Core Files

- **`bot.py`** - Main entry point
  - Bot initialization with command/event handlers
  - Standard and Molda voice channel commands

- **`config.py`** - Configuration management
  - Loads `.env` variables: `DISCORD_TOKEN`, `MONITORED_ROLE_ID`, `VOICE_CHANNEL_ID`, `MOLDA_CHANNEL_ID`, `JOIN_PLAY_DELAY`, `MOLDA_REJOIN_INTERVAL`

- **`utils.py`** - Utility functions
  - `has_role(member, role_id)` - Check member roles
  - `find_recent_mute_actor(guild, target)` - Find who muted a user via audit logs

- **`voice_commands.py`** - Voice operations
  - `join_voice()` - Join channel by ID with retry logic
  - `leave_voice()` - Leave current channel
  - `play_join()` - Play audio file in voice channel
  - Connection pooling and validation

- **`events.py`** - Event handlers
  - `on_ready()` - Auto-join with exponential backoff retries
  - `on_voice_state_update()` - Auto-unmute after server mute + join audio playback
  - Molda auto-rejoin loop (hourly reconnection)

- **`greetings.py`** - Per-member greeting system
  - Dynamic commands from `Molda Voice/` directory
  - Member-specific audio files

- **`audio_encoder.py`** - Audio preprocessing
  - MP3 → Opus encoding for efficiency
  - On-startup pre-encoding

- **`ffmpeg_helper.py`** - FFmpeg management
  - Auto-download static FFmpeg build if needed
  - Supports `FFMPEG_PATH` environment variable

### Configuration Files

- **`requirements.txt`** - Python dependencies
- **`runtime.txt`** - Python 3.11 version
- **`railway.toml`** - Railway deployment config (Opus package, Nixpacks builder)
- **`Procfile`** - Railway startup command
- **`.env`** - Environment variables (local only):
  ```
  DISCORD_TOKEN=your_bot_token
  MONITORED_ROLE_ID=role_id_to_monitor
  VOICE_CHANNEL_ID=channel_id_for_auto_join (optional)
  MOLDA_CHANNEL_ID=molda_channel_id (optional)
  JOIN_PLAY_DELAY=3.0 (seconds, optional)
  MOLDA_REJOIN_INTERVAL=3600 (seconds, optional)
  FFMPEG_PATH=/path/to/ffmpeg (optional)
  
  # Per-member greeting tokens (optional)
  ALEX=member_id
  IVAN=member_id
  MAKSYM=member_id
  MOLDA=member_id
  NAZAR=member_id
  SASHA=member_id
  YURA=member_id
  REPEAT=member_id
  SPECIFIC=member_id
  NEW_COMERS=member_id
  ```

# Features

## Voice Commands (Admin Only)

### Channel Management
- `!join-channel <channel_id>` - Join voice channel with retries
- `!leave-channel` - Leave current channel
- `!join-channel-molda <channel_id>` - Join with hourly auto-rejoin enabled
- `!leave-channel-molda` - Leave and disable auto-rejoin

### Audio Playback
- `!play-join [filename]` - Play audio file from `Molda Voice/` folder
- `!current-audio-stop` - Stop current audio playback
- `!encode-audio` - Pre-encode all MP3s to Opus format for efficiency

### Greeting Commands (Dynamic)

Auto-generated from audio files in `Molda Voice/` matching pattern `*_Molda.(mp3|opus)`:

**Available greetings** (command format: `!play-audio-greeting-<name>`):
- `!play-audio-greeting-alex` → Alex_Molda.opus
- `!play-audio-greeting-ivan` → Ivan_Molda.opus
- `!play-audio-greeting-maksym` → Maksym_Molda.opus
- `!play-audio-greeting-molda` → Molda_Molda.opus
- `!play-audio-greeting-nazar` → Nazar_Molda.opus
- `!play-audio-greeting-new_comers` → New_comers_molda.opus
- `!play-audio-greeting-repeat` → Repeat_Molda.opus
- `!play-audio-greeting-sasha` → Sasha_Molda.opus
- `!play-audio-greeting-specific` → Specific_Molda.opus
- `!play-audio-greeting-yura` → Yura_Molda.opus

**Per-Member Greetings** (set via `.env` tokens):
- Set `ALEX=<member_id>` to auto-play Alex_Molda when that member joins
- Set `IVAN=<member_id>` to auto-play Ivan_Molda when that member joins
- Same for other names: `MAKSYM`, `MOLDA`, `NAZAR`, `SASHA`, `YURA`, `REPEAT`, `SPECIFIC`, `NEW_COMERS`

## Auto-Features

- Auto-join configured voice channel on startup (with retries)
- Auto-play join audio when users enter
- Auto-unmute after 5 seconds when muted by monitored role
- Molda channel auto-rejoin every hour (if enabled)
- MP3 → Opus audio encoding for efficiency