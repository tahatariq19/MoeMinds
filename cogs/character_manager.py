import discord
from discord.ext import commands
from discord import app_commands
from config import CHARACTER_PROFILES

class CharacterManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='list_characters', description='View all available character personalities.')
    async def list_characters(self, interaction: discord.Interaction):
        if CHARACTER_PROFILES:
            character_names = sorted([name.capitalize() for name in CHARACTER_PROFILES.keys()])
            characters_list = "\n".join(character_names)
            await interaction.response.send_message(f"**Available Character Personalities:**\n```\n{characters_list}\n```\nUse `/set_character <name>` to choose one.")
        else:
            await interaction.response.send_message("No character personalities are currently defined.")

    @app_commands.command(name='define_character', description='Define a new custom character personality.')
    @app_commands.describe(
        character_name="The name for your new character (e.g., 'wise old wizard')",
        description="A detailed description of the character's personality for the AI to mimic."
    )
    async def define_character(self, interaction: discord.Interaction, character_name: str, description: str):
        if character_name.lower() in CHARACTER_PROFILES:
            await interaction.response.send_message(f"A character with the name '{character_name}' already exists. Please choose a different name.")
        else:
            CHARACTER_PROFILES[character_name.lower()] = {
                "description": description,
                "name_aliases": [character_name.lower()]
            }
            await interaction.response.send_message(
                f"Character **'{character_name.capitalize()}'** has been successfully defined! "
                f"You can now switch to this personality using `/set_character {character_name.lower()}`."
            )

async def setup(bot):
    await bot.add_cog(CharacterManager(bot))
