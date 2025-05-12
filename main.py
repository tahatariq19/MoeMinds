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

# --- AI Response Generation ---

async def generate_ai_response(user_id, user_message_content, user_display_name):
    """
    Generates an AI response based on character personality and conversation history.
    """
    user_data = await get_user_data(user_id)
    character_name = user_data.get('character', DEFAULT_CHARACTER)
    chat_history = user_data.get('history', []) # This will now store formatted chat entries

    character_profile = CHARACTER_PROFILES.get(character_name.lower(), CHARACTER_PROFILES[DEFAULT_CHARACTER])
    
    # Modify the system instruction to include the user's name and length guidance
    system_instruction = (
        f"{character_profile['description']} You are talking to a user named {user_display_name}. "
        "Keep your responses concise and to the point, but provide more detail if the conversation requires it. "
        "Aim to match the general length and depth of the user's messages, rather than always providing verbose answers."
    )

    # The history passed to start_chat should directly be the stored chat_history
    # since it's already in the correct format.
    # Add system instruction as the very first message if chat_history is empty
    initial_history = []
    if not chat_history: # Only add system instruction if starting a new chat or after a manual reset
        initial_history.append({'role': 'user', 'parts': [{'text': system_instruction}]})
        initial_history.append({'role': 'model', 'parts': [{'text': "Understood. I will now respond as specified."}]})

    # Add the current user message
    new_message = {'role': 'user', 'parts': [{'text': user_message_content}]}

    try:
        # Start a new chat session with the full historical context
        # If initial_history exists, it primes the model with personality
        chat = client.chats.create(model='gemini-2.5-flash-lite-preview-06-17', history=initial_history + chat_history)

        # Send only the new user message
        response = await asyncio.to_thread(chat.send_message, user_message_content)
        ai_response = response.text

        # Update chat history with both the user's message and the AI's response
        chat_history.append(new_message)
        chat_history.append({'role': 'model', 'parts': [{'text': ai_response}]})

        # Keep only the last MAX_HISTORY_LENGTH interactions (each interaction is 2 messages: user+model)
        # We need to slice in pairs if we're doing it this way
        user_data['history'] = chat_history[-MAX_HISTORY_LENGTH * 2:] 
        await update_user_data(user_id, user_data)

        return ai_response
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "I am unable to respond right now. Please try again later."

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

@bot.event
async def on_message(message):
    """
    Handles incoming messages to the Discord bot for active engagement or mentions.
    Slash commands are handled by their respective decorators and do not pass through here.
    """
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # No need to process prefix commands as they are removed.
    # The bot will only respond to mentions or active engagement now, besides slash commands.

    user_id = str(message.author.id)
    user_data = await get_user_data(user_id)
    active_engagement = user_data.get('active_engagement', False)
    current_time = time.time()
    
    # Get the user's display name
    user_display_name = message.author.display_name

    respond_to_message = False

    # Check for active engagement or mentions
    if bot.user.mentioned_in(message):
        respond_to_message = True
    elif active_engagement:
        # Check cooldown for active engagement to prevent spam
        if user_id not in last_message_times or (current_time - last_message_times[user_id]) > ACTIVE_ENGAGEMENT_COOLDOWN:
            respond_to_message = True
            last_message_times[user_id] = current_time

    if respond_to_message:
        # Generate AI response, passing the user's display name
        async with message.channel.typing(): # Show "bot is typing..."
            ai_response = await generate_ai_response(user_id, message.content, user_display_name)
            await message.channel.send(ai_response)


# --- Discord Bot Slash Commands ---

@bot.tree.command(name='set_character', description='Set the bot\'s personality.')
@app_commands.describe(character_name="The name of the character personality to set (e.g., 'makise kurisu', 'erza scarlet', 'ed')")
async def set_character(interaction: discord.Interaction, character_name: str):
    """
    Sets the AI's personality to a specified character using a slash command.
    Upon setting, the history is reset and immediately primed with the new character's instruction.
    """
    user_id = str(interaction.user.id)
    if character_name.lower() in CHARACTER_PROFILES:
        user_data = await get_user_data(user_id)
        user_data['character'] = character_name.lower()
        
        # Clear history when character changes to avoid context issues
        user_data['history'] = []
        
        # Explicitly prime the history with the new character's system instruction
        character_profile = CHARACTER_PROFILES.get(character_name.lower(), CHARACTER_PROFILES[DEFAULT_CHARACTER])
        system_instruction = (
            f"{character_profile['description']} You are talking to a user named {interaction.user.display_name}. "
            "Keep your responses concise and to the point, but provide more detail if the conversation requires it. "
            "Aim to match the general length and depth of the user's messages, rather than always providing verbose answers."
        )
        user_data['history'].append({'role': 'user', 'parts': [{'text': system_instruction}]})
        user_data['history'].append({'role': 'model', 'parts': [{'text': "Understood. I will now respond as specified."}]})

        await update_user_data(user_id, user_data)
        await interaction.response.send_message(f"My personality has been set to **{character_name.capitalize()}** for you, {interaction.user.mention}!")
        await interaction.followup.send(f"Conversation history has been reset, and I'm ready to chat as **{character_name.capitalize()}**!")
    else:
        available_characters = ", ".join([name.capitalize() for name in CHARACTER_PROFILES.keys()])
        await interaction.response.send_message(f"Sorry, I don't know that character. Available characters: {available_characters}")

@bot.tree.command(name='toggle_engagement', description='Toggle active conversation engagement (on/off).')
async def toggle_engagement(interaction: discord.Interaction):
    """
    Toggles the active conversation engagement mode for the user using a slash command.
    """
    user_id = str(interaction.user.id)
    user_data = await get_user_data(user_id)
    user_data['active_engagement'] = not user_data.get('active_engagement', False)
    await update_user_data(user_id, user_data)
    status = "ON" if user_data['active_engagement'] else "OFF"
    await interaction.response.send_message(f"Active conversation engagement for {interaction.user.mention} is now: **{status}**.")
    if status == "OFF":
        await interaction.followup.send("I will now only respond when directly mentioned (@BotName).")
    else:
        await interaction.followup.send("I will now actively engage in conversation (with a cooldown to prevent spam).")

@bot.tree.command(name='reset_chat', description='Resets your conversation history with the bot.')
async def reset_chat(interaction: discord.Interaction):
    """
    Resets the conversation history for the requesting user using a slash command.
    """
    user_id = str(interaction.user.id)
    user_data = await get_user_data(user_id)
    user_data['history'] = []
    # After reset, prime the history with the current character's system instruction
    character_name = user_data.get('character', DEFAULT_CHARACTER)
    character_profile = CHARACTER_PROFILES.get(character_name.lower(), CHARACTER_PROFILES[DEFAULT_CHARACTER])
    system_instruction = (
        f"{character_profile['description']} You are talking to a user named {interaction.user.display_name}. "
        "Keep your responses concise and to the point, but provide more detail if the conversation requires it. "
        "Aim to match the general length and depth of the user's messages, rather than always providing verbose answers."
    )
    user_data['history'].append({'role': 'user', 'parts': [{'text': system_instruction}]})
    user_data['history'].append({'role': 'model', 'parts': [{'text': "Understood. I will now respond as specified."}]})

    await update_user_data(user_id, user_data)
    await interaction.response.send_message(f"Your conversation history has been reset, {interaction.user.mention}. We can start fresh!")


# --- Run the bot ---
if __name__ == '__main__':
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Failed to start Discord bot: {e}")
        print("Please ensure your DISCORD_BOT_TOKEN is correct and has 'Message Content Intent' enabled.")
