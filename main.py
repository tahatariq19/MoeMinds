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
