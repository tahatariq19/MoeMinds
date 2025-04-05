import discord
import os

# --- Discord Bot Configuration ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# --- Run the bot ---
if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)