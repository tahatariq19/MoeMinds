import discord
from discord.ext import commands
from config import DISCORD_BOT_TOKEN

#Define intents - Crucial for receiving message content
intents = discord.Intents.default()
intents.message_content = True # Enable message content intent for regular message processing
intents.members = True # Enable members intent for user information

# Initialize the bot without a command_prefix for slash command exclusive operation
bot = commands.Bot(command_prefix=lambda bot, message: [], intents=intents)

# --- Discord Bot Events ---
@bot.event
async def on_ready():
    """
    Confirms when the bot is online and ready and syncs slash commands.
    """
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # Load cogs
    await bot.load_extension("cogs.ai_commands")
    await bot.load_extension("cogs.character_manager")

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
