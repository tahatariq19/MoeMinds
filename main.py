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

@bot.tree.command(name='my_character', description='Shows your current character personality.')
async def my_character(interaction: discord.Interaction):
    """
    Shows the user their currently set character personality using a slash command.
    """
    user_id = str(interaction.user.id)
    user_data = await get_user_data(user_id)
    character = user_data.get('character', DEFAULT_CHARACTER).capitalize()
    await interaction.response.send_message(f"Your current character personality is set to: **{character}**.")

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