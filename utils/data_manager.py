from config import DEFAULT_CHARACTER

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
