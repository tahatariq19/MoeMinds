### How to Use and Run the Bot:

1.  **Save the Code**: Save the code above as a Python file (e.g., `discord_bot.py`).
2.  **Install Libraries**: Open your terminal or command prompt and install the required libraries:
    ```bash
    pip install discord.py google-generativeai python-dotenv
    ```
3.  **Environment Variables**: Create a `.env` file in the same directory as your `main.py` and add your Discord bot token and Gemini API key:
    ```
    DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN_HERE"
    AI_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```
    Replace `"YOUR_DISCORD_BOT_TOKEN_HERE"` and `"YOUR_GEMINI_API_KEY_HERE"` with your actual tokens.
4.  **Run the Bot**: Execute the Python script from your terminal:
    ```bash
    python main.py
    ```
    You should see output similar to `Logged in as YourBotName#1234 (ID: ...)`
5.  **Interact on Discord**: Go to your Discord server where the bot was invited.

### Bot Commands (Slash Commands):

* `/set_character <character_name>`: Sets the bot's personality for your conversations.
    * Example: `/set_character Makise Kurisu`
    * Example: `/set_character Erza Scarlet`
    * If you set a new character, your conversation history with the bot for that character will be reset.
* `/toggle_engagement`: Toggles whether the bot actively engages in conversation or only responds when mentioned/commanded.
* `/reset_chat`: Clears your personal conversation history with the bot. This is useful if the bot gets stuck in a loop or you want a fresh start.
* `/my_character`: Shows the current character personality assigned to you.
* `/list_characters`: View all available character personalities.
* `/define_character <character_name> <description>`: Define a new custom character personality.

### Explanation of Features:

*   **Personality Mimicry**: When you use `/set_character`, the bot's internal prompt for the AI model is updated with the detailed personality description of the chosen character. This guides the AI to respond in a way consistent with that character.
*   **AI Conversation**: The `google-generativeai` library is used to interact with the `gemini-2.0-flash` model. Each user's messages and the bot's replies are sent to the AI to maintain context within the conversation.
*   **Information Retention (In-memory)**:
    *   All user data (history, character, active_engagement) is stored in-memory and will be lost when the bot restarts.
    *   The `get_user_data` and `update_user_data` asynchronous functions handle reading from and writing to this in-memory store.
    *   The history is limited to `MAX_HISTORY_LENGTH` (default 20) to keep the context manageable for the AI model and reduce token usage.
*   **Active Engagement Toggle**:
    *   The `/toggle_engagement` command changes a boolean flag stored in-memory for each user.
    *   When active engagement is `ON`, the bot will respond to most messages in the channel (from that user), subject to a `ACTIVE_ENGAGEMENT_COOLDOWN` (default 2 seconds) to prevent excessive replies.
    *   When `OFF`, the bot will only respond if it's directly mentioned (e.g., `@YourBotName How are you?`) or if you use a command (e.g., `/reset_chat`).
*   **Asynchronous Operations**: The bot uses `asyncio` and `await` for Discord operations and for making API calls to the Gemini model. This prevents the bot from freezing while waiting for responses.

Feel free to customize `CHARACTER_PROFILES` to add more personalities!
