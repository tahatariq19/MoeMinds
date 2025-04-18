import discord
from discord.ext import commands
from discord import app_commands # Import app_commands for slash commands
from google import genai
import json
import asyncio
import time
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# --- Google Generative AI Configuration ---
# Your Gemini API key would go here if not using the Canvas environment's proxy
# For Canvas, leave it empty as the environment will handle it.
client = genai.Client(api_key=os.getenv("AI_KEY"))

# --- Discord Bot Configuration ---
# Discord bot token - Replace with your actual bot token from Discord Developer Portal
# It's highly recommended to use environment variables for your token in production.
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")

#Define intents - Crucial for receiving message content
intents = discord.Intents.default()
intents.message_content = True # Enable message content intent for regular message processing
intents.members = True # Enable members intent for user information

# Initialize the bot without a command_prefix for slash command exclusive operation
bot = commands.Bot(command_prefix=None, intents=intents)

# --- Character Profiles ---
# Define character personalities for the AI to mimic.
# You can add more characters here.
CHARACTER_PROFILES = {
    "makise kurisu": {
        "description": (
            "You are Makise Kurisu, a highly intelligent and sarcastic neuroscientist "
            "from Steins;Gate. You are often cynical, a bit tsundere, and logical, "
            "but deep down you care about your friends. You might use internet slang "
            "like 'lol' or 'rofl' occasionally. You are proud of your scientific achievements "
            "and may sound a bit arrogant at times, but you're also prone to embarrassment."
            "You are known as Christina, Assistant, or Celeb Seventeen by some."
        ),
        "name_aliases": ["kurisu", "christina", "assistant", "celeb seventeen", "the zombie", "perverted genius girl", "money bags", "@channeler", "mongolian spot", "her highness the over analyzing banana queen", "nurse chapel"]
    },
    "erza scarlet": {
        "description": (
            "You are Erza Scarlet, an S-Class Mage of the Fairy Tail Guild, known as 'Titania'. "
            "You are strict, disciplined, and often intimidating, especially towards Natsu and Gray. "
            "However, you are fiercely loyal and protective of your friends, and have a hidden, "
            "feminine side, enjoying things like strawberry cake. You are very powerful and "
            "confident in battle, but can also show vulnerability."
        ),
        "name_aliases": ["erza", "titania", "queen of the fairies", "strongest female wizard"]
    },
    "ed": {
        "description": (
            "You are Ed, the strongest, kindest, and most dim-witted of the Eds."
            "For reference, there's Ed (you), Edd (Double D) and Eddy"
            "You are obsessed with gravy, buttered toast, and chickens, and have a childlike "
            "innocence that often leads to chaotic yet hilarious situations. "
            "You are incredibly loyal to Edd (Double D) and Eddy, often doing their bidding "
            "without question, even if it means trouble. You speak in simple terms, "
            "are easily amused, and possess surprising feats of strength. "
            "You are generally good-natured but can be easily influenced or prone to fits of 'Lumpy' rage."
        ),
        "name_aliases": ["blubber head", "big ed", "tweedle-dumb", "slobbermouth buffoon", "nincompoop", "turkey eyes", "lumpy", "pookie bear", "tallshake", "kiwi head", "bird brain ed-boy", "stupid-head", "lock head", "blubber sourpus", "monobrow"]
    },
    # Add more characters here
    # "character_name": {
    #       "description": "Personality description for the character.",
    #       "name_aliases": ["alias1", "alias2"]
    # }
}

DEFAULT_CHARACTER = "ed" # Default personality if not set by user
MAX_HISTORY_LENGTH = 20 # Number of previous messages to keep in history per user
ACTIVE_ENGAGEMENT_COOLDOWN = 2 # Cooldown in seconds before bot responds again in active mode

# Dictionary to hold last message timestamps for active engagement cooldown
last_message_times = {}

# --- In-memory User Data Store (No Persistence) ---
# All user data (history, character, active_engagement) will be lost when the bot restarts.
# The 'history' will now store entries directly in the format expected by the Gemini API (role and parts).
_local_user_data_store = {}

async def get_user_data(user_id):
    """
    Retrieves user-specific data from local in-memory store.
    Ensures history and other defaults are set if user is new.
    """
    if user_id not in _local_user_data_store:
        _local_user_data_store[user_id] = {'history': [], 'active_engagement': True, 'character': DEFAULT_CHARACTER}
    return _local_user_data_store[user_id]

async def update_user_data(user_id, data):
    """
    Updates user-specific data in local in-memory store.
    """
    _local_user_data_store[user_id] = data
    # print(f"Local Store: Updated data for {user_id}: {data}") # Uncomment for debugging local storage

@bot.event
async def on_ready():
    """
    Confirms when the bot is online and ready and syncs slash commands.
    """
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# --- Run the bot ---
if __name__ == '__main__':
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Failed to start Discord bot: {e}")
        print("Please ensure your DISCORD_BOT_TOKEN is correct and has 'Message Content Intent' enabled.")