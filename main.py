import discord
from discord.ext import commands
from discord import app_commands # Import app_commands for slash commands
from google import genai
import json
import asyncio
import time
import os

#Define intents - Crucial for receiving message content
intents = discord.Intents.default()
intents.message_content = True # Enable message content intent for regular message processing
intents.members = True # Enable members intent for user information

# Initialize the bot without a command_prefix for slash command exclusive operation
bot = commands.Bot(command_prefix=None, intents=intents)

# --- Discord Bot Events ---

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

@bot.tree.command(name='list_characters', description='View all available character personalities.')
async def list_characters(interaction: discord.Interaction):
    """
    Lists all available character personalities that users can choose from.
    """
    if CHARACTER_PROFILES:
        character_names = sorted([name.capitalize() for name in CHARACTER_PROFILES.keys()])
        characters_list = "\n".join(character_names)
        await interaction.response.send_message(f"**Available Character Personalities:**\n```\n{characters_list}\n```\nUse `/set_character <name>` to choose one.")
    else:
        await interaction.response.send_message("No character personalities are currently defined.")

@bot.tree.command(name='define_character', description='Define a new custom character personality.')
@app_commands.describe(
    character_name="The name for your new character (e.g., 'wise old wizard')",
    description="A detailed description of the character's personality for the AI to mimic."
)
async def define_character(interaction: discord.Interaction, character_name: str, description: str):
    """
    Allows a user to define a new custom character personality for the AI.
    """
    if character_name.lower() in CHARACTER_PROFILES:
        await interaction.response.send_message(f"A character with the name '{character_name}' already exists. Please choose a different name.")
    else:
        # Add the new character to the CHARACTER_PROFILES dictionary
        CHARACTER_PROFILES[character_name.lower()] = {
            "description": description,
            "name_aliases": [character_name.lower()] # Start with the given name as an alias
        }
        await interaction.response.send_message(
            f"Character **'{character_name.capitalize()}'** has been successfully defined! "
            f"You can now switch to this personality using `/set_character {character_name.lower()}`."
        )
        # Optionally, you might want to force a resync of commands if character options are dynamic
        # For now, it's enough that the character exists in the dictionary.


# --- Run the bot ---
if __name__ == '__main__':
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Failed to start Discord bot: {e}")
        print("Please ensure your DISCORD_BOT_TOKEN is correct and has 'Message Content Intent' enabled.")