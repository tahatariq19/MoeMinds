import discord
from discord.ext import commands
from discord import app_commands
import time
from config import CHARACTER_PROFILES, DEFAULT_CHARACTER, ACTIVE_ENGAGEMENT_COOLDOWN
from utils.data_manager import get_user_data, update_user_data, last_message_times
from utils.ai_utils import generate_ai_response

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        user_id = str(message.author.id)
        user_data = await get_user_data(user_id)
        active_engagement = user_data.get('active_engagement', False)
        current_time = time.time()
        
        user_display_name = message.author.display_name

        respond_to_message = False

        if self.bot.user.mentioned_in(message):
            respond_to_message = True
        elif active_engagement:
            if user_id not in last_message_times or (current_time - last_message_times[user_id]) > ACTIVE_ENGAGEMENT_COOLDOWN:
                respond_to_message = True
                last_message_times[user_id] = current_time

        if respond_to_message:
            async with message.channel.typing():
                ai_response = await generate_ai_response(user_id, message.content, user_display_name)
                await message.channel.send(ai_response)

    @app_commands.command(name='set_character', description='Set the bot\'s personality.')
    @app_commands.describe(character_name="The name of the character personality to set (e.g., 'makise kurisu', 'erza scarlet', 'ed')")
    async def set_character(self, interaction: discord.Interaction, character_name: str):
        user_id = str(interaction.user.id)
        if character_name.lower() in CHARACTER_PROFILES:
            user_data = await get_user_data(user_id)
            user_data['character'] = character_name.lower()
            
            user_data['history'] = []
            
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

    @app_commands.command(name='toggle_engagement', description='Toggle active conversation engagement (on/off).')
    async def toggle_engagement(self, interaction: discord.Interaction):
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

    @app_commands.command(name='reset_chat', description='Resets your conversation history with the bot.')
    async def reset_chat(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = await get_user_data(user_id)
        user_data['history'] = []
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

    @app_commands.command(name='my_character', description='Shows your current character personality.')
    async def my_character(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = await get_user_data(user_id)
        character = user_data.get('character', DEFAULT_CHARACTER).capitalize()
        await interaction.response.send_message(f"Your current character personality is set to: **{character}**.")

async def setup(bot):
    await bot.add_cog(AICommands(bot))
