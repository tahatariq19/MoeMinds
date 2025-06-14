# MoeMinds: Your Discord Bot with Personality! ✨

Welcome to MoeMinds, a Discord bot designed to bring beloved animated characters to life! Chat with a delightful cast of diverse personalities, each ready for engaging and dynamic conversations.

## Getting Started 🚀

To run MoeMinds, you'll need your own Gemini API key. Ready to bring MoeMinds to your Discord server? Follow these simple steps:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/tahatariq19/MoeMinds.git
    cd moe-minds
    ```
2.  **Set up Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.

    *   **Create Virtual Environment:**
        ```bash
        python -m venv venv
        ```
    *   **Activate Virtual Environment:**
        *   **Windows:**
            ```bash
            .\venv\Scripts\activate # OR activate.ps1 if using powershell
            ```
        *   **macOS/Linux:**
            ```bash
            source venv/bin/activate
            ```
3.  **Install Libraries:** Make sure you have Python installed, then grab the necessary libraries:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Environment Variables:** Create a `.env` file by copying and filling out the provided `.env.example` in the root directory of your project (where `main.py` is located). Add your Discord bot token and Gemini API key:
    ```
    DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN_HERE"
    AI_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```
    *(Don't forget to replace the placeholders with your actual tokens!)*
5.  **Run the Bot:** Fire up the bot from your terminal:
    ```bash
    python main.py
    ```
    You should see a confirmation message like `Logged in as YourBotName#1234 (ID: ...)` in your console. 🎉
6.  **Chat Away!** Head over to your Discord server where the bot is invited and start interacting!

## Bot Commands (Slash Commands) 🤖

MoeMinds uses easy-to-use slash commands. Just type `/` in your Discord chat to see the options!

*   `/set_character <character_name>`: Choose who you want to chat with! Sets the bot's personality for your conversations.
    *   Example: `/set_character Makise Kurisu`
    *   Example: `/set_character Ed`
    *   *(Note: Changing characters will reset your conversation history with the bot for a fresh start!)*
*   `/toggle_engagement`: Decide how chatty MoeMinds should be! Toggles whether the bot actively engages in conversation or only responds when mentioned.
*   `/reset_chat`: Need a clean slate? Clears your personal conversation history with the bot.
*   `/my_character`: Curious who you're talking to? Shows your current character personality.
*   `/list_characters`: See all the amazing personalities MoeMinds can embody!
*   `/define_character <character_name> <description>`: Feeling creative? Define a brand new custom character personality for the AI to mimic!

## How MoeMinds Works (Under the Hood) 🧠

*   **Personality Power:** When you `/set_character`, the bot's AI model is updated with a detailed personality description, guiding its responses to match your chosen character.
*   **Smart Conversations:** MoeMinds uses the `google-generativeai` library to chat with the Gemini model, keeping your conversation history in mind for seamless interactions.
*   **Memory Magic (In-memory):** Your conversation history and character preferences are stored in-memory. This means they'll reset if the bot restarts, but it keeps things snappy!
*   **Active Engagement:** The `/toggle_engagement` command lets you control how much MoeMinds participates in chat, with a built-in cooldown to prevent spam.
*   **Smooth Operator:** Built with `asyncio`, MoeMinds handles Discord operations and AI calls asynchronously, ensuring a smooth and responsive experience.

## Configuration ⚙️

Want to customize MoeMinds even further? You can tweak its core settings in `config.py`:

*   **AI Model:** Change the `GEMINI_MODEL` variable to use a different Gemini model (e.g., `gemini-2.5-pro`).
*   **Character Personalities:** The `CHARACTER_PROFILES` dictionary holds all the predefined personalities. You can:
    *   Modify existing character descriptions to fine-tune their behavior.
    *   Add new characters by following the existing format.
    *   Adjust `DEFAULT_CHARACTER` to set a different default personality.
*   **Conversation History Length:** `MAX_HISTORY_LENGTH` controls how many previous messages (user + bot) are kept in memory for context. Adjust this to balance context and token usage.
*   **Active Engagement Cooldown:** `ACTIVE_ENGAGEMENT_COOLDOWN` (in seconds) prevents the bot from spamming responses when active engagement is enabled. Increase this value if the bot is too chatty.

Have fun chatting with your favorite characters! If you have ideas for more personalities, feel free to add them!
