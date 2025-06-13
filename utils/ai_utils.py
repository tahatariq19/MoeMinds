import asyncio
from google import genai
from config import CHARACTER_PROFILES, DEFAULT_CHARACTER, MAX_HISTORY_LENGTH, AI_KEY, GEMINI_MODEL
from utils.data_manager import get_user_data, update_user_data

client = genai.Client(api_key=AI_KEY)

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
        chat = client.chats.create(model=GEMINI_MODEL, history=initial_history + chat_history)

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
