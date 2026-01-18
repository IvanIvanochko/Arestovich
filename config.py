import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MONITORED_ROLE_ID = int(os.getenv("MONITORED_ROLE_ID", "0"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", "0"))
