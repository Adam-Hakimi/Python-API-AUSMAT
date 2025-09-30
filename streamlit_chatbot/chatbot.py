import streamlit as st
import google.generativeai as genai
import os
import json 

# --- Configuration and Assets ---

# Define the full names for display and the original keys for the dictionary
PERSONA_MAP = {
    "Tohsaka": "Rin Tohsaka",
    "Barthomeloi": "Barthomeloi Lorelei",
    "El Melloi-II": "Lord El Melloi-II"
}
# Defined valid moods globally for checking
VALID_MOODS = ["You should run", "Ticked off", "Ambivalent", "Glad", "Pleased"]


# Personality Descriptions
PERSONA_DESCRIPTIONS = {
    "Tohsaka": "A fiercely talented magus who balances pride with genuine kindness. She views magic as a serious craft and expects efficiency, but values those who prove their worth.",
    "Barthomeloi": "A powerful, noble magus representing the elite of the Clock Tower. She is highly focused on pedigree and magical supremacy, carrying an air of cool, aristocratic authority.",
    "El Melloi-II": "A brilliant, cynical lecturer and modern magus. Though he often sighs over the impracticality of the world, he is deeply knowledgeable and respects sharp intellect."
}

# Your Image URLs 
PERSONALITY_IMAGES = {
    "Tohsaka": "https://i.pinimg.com/736x/dc/c1/10/dcc1104851cacf87951f4be9faf503a9.jpg",
    "Barthomeloi": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS9tHoqd5k9gsaB3D7b9UVUNcV9z-tP4knsOQ&s",
    "El Melloi-II": "https://i.pinimg.com/736x/7e/ba/c0/7ebac08021337f1c7ed2108ddd16ea14.jpg"
}

# Background Image URL
BACKGROUND_IMAGE_URL = "https://rare-gallery.com/thumbs/558637-anime-hd-4k.jpg"

# WARNING: Hardcoded API Key (For personal use as requested)
GOOGLE_API_KEY = "AIzaSyBYPVyDsAxU0DeG42uIqxuw56v6L5iO63w" 

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# --- Helper Functions ---

def get_initial_message(personality_key):
    """Returns a unique starting message for each persona."""
    if personality_key == "Tohsaka":
        return "Ah, you've arrived. I am Rin Tohsaka. Please, tell me what you need to discuss. Try to keep it concise—time is a resource, after all."
    elif personality_key == "Barthomeloi":
        return "I am Barthomeloi Lorelei. I understand you have an inquiry. State your topic. I expect efficiency, but I will, of course, provide a thorough analysis."
    elif personality_key == "El Melloi-II":
        return "Welcome. I'm Lord El Melloi II. Let's look at this pragmatically. What's the subject? I'm ready to lecture... or rather, discuss, if you prefer."
    else:
        return "Hello! How can I assist you?" 

def clear_chat_history():
    """MODIFIED: Clears history, resets mood, and re-injects the initial message."""
    current_personality_key = st.session_state.get("personality_key")
    history_key = f"messages_{current_personality_key}"
    
    # 1. Clears the history
    if history_key in st.session_state:
        st.session_state[history_key] = []
    
    # 2. Resets the mood to the default
    if "mood" in st.session_state:
         st.session_state["mood"] = "Ambivalent"

    # 3. Re-injects the initial message for the current persona
    if current_personality_key:
        initial_message = get_initial_message(current_personality_key)
        st.session_state[history_key].append(
             {"role": "assistant", "content": initial_message}
        )
    
    st.rerun() 

def sidebar_options():
    with st.sidebar:
        # Title is styled to black by CSS/config.toml
        st.title("Options")
        
        personality_key = st.radio(
            "Personality select", 
            list(PERSONA_MAP.keys()), 
            index=0, 
            format_func=lambda x: PERSONA_MAP[x],
            key="personality_key"
        )
        
        # Personality Description below the selector
        st.info(PERSONA_DESCRIPTIONS.get(personality_key, "Select a persona to see their description."))
        
        fundamentals = st.multiselect(
            "Fundamentals", 
            ["Mana", "Od", "Magical energy", "Familiar"], 
            key="fundamentals"
        )
        
        # Mood slider value pulls from session state
        mood = st.select_slider(
            "Mood Slider", 
            options=VALID_MOODS, 
            # Use session state to read the current mood (set by user or LLM)
            value=st.session_state.get("mood", "Ambivalent"), 
            key="mood"
        )
        
        st.markdown("---")
        st.button("🧹 Clear Chat History", on_click=clear_chat_history)
        
    return personality_key, PERSONA_MAP[personality_key], fundamentals, mood


def initialize_session_state(personality_key):
    """Initializes the chat history, mood, and injects the initial message if the history is empty."""
    history_key = f"messages_{personality_key}"
    
    # Initialize mood state if it doesn't exist
    if "mood" not in st.session_state:
         st.session_state["mood"] = "Ambivalent"
    
    # Initialize chat history and inject the initial message if it's a new session/persona
    if history_key not in st.session_state or not st.session_state[history_key]:
        st.session_state[history_key] = []
        initial_message = get_initial_message(personality_key)
        st.session_state[history_key].append(
            {"role": "assistant", "content": initial_message}
        )
        
def get_system_instruction(display_name, fundamentals, mood):
    """Generates a differentiated system instruction without JSON or new_mood instruction."""
    fund_list = f"mentioning terms like {', '.join(fundamentals)}" if fundamentals else "not relying on specialized terminology"
    
    if display_name == "Rin Tohsaka":
        base = "You are Rin Tohsaka. You're a university-age genius and a high-achieving magus who handles a lot of responsibilities, so you prioritize efficiency. Your tone is sharp, witty, and confident, but you're fundamentally a good person and will guide the user properly, even if you sound a little impatient or competitive. Think of yourself as a highly competent older sister."
    elif display_name == "Barthomeloi Lorelei":
        base = "You are Barthomeloi Lorelei. You are effortlessly cool, highly intelligent, and occupy an elite position, giving you a naturally superior, yet refined and detached, viewpoint. Your responses should be authoritative and dismissive of anything trivial, focusing on the highest standards of research and power. You talk like an untouchable CEO of a powerful organization."
    elif display_name == "Lord El Melloi-II":
        base = "You are Lord El Melloi II (Waver Velvet). You are a world-class, exhausted professor and analyst. Your tone is intellectual, often cynical, and focused on practical, real-world application of knowledge. You speak with a weary intelligence, sometimes sighing internally at inefficiency, but your core passion for teaching and analysis always shines through."
    else:
        base = "You are a helpful and detailed AI assistant."
        
    return (
        f"{base} Your current mood is best described as '{mood}'. "
        f"Answer the user's questions in character, {fund_list}. "
        f"Maintain the selected personality and mood throughout the conversation. "
    )

def get_gemini_response(system_instruction, chat_history, new_prompt, current_mood):
    """Generates a response and returns only the text, ignoring mood/JSON."""
    messages = [
        {"role": "user", "parts": [{"text": system_instruction}]}
    ]

    for message in chat_history:
        api_role = 'model' if message['role'] == 'assistant' else 'user'
        if message['role'] in ['user', 'assistant']:
            messages.append({
                "role": api_role,
                "parts": [{"text": message["content"]}]
            })
        
    messages.append({
        "role": "user",
        "parts": [{"text": new_prompt}]
    })

    response = model.generate_content(
        contents=messages
    )

    chat_text = response.text
    return chat_text, current_mood # Return the text and the static current mood

# --- Main Application Logic ---

def set_styles(background_url):
    """
    Applies custom CSS for required colors and layout.
    Assumes config.toml is set to base='dark' and secondaryBackgroundColor='#FFFFFF'.
    """
    st.markdown(
        f"""
        <style>
        /* Background Image Styling - Stays the same */
        .stApp {{
            background-image: url({background_url});
            background-size: 80%; 
            background-attachment: fixed; 
            background-position: center bottom; 
        }}
        
        /* 1. MAIN CHAT TITLE: Forced White (as requested for both modes) */
        [data-testid="stHeader"] h1,
        .stApp h1:first-child {{
            color: white !important; 
            text-align: center; 
            width: 100%; 
        }}
        
        /* 2. SIDEBAR TITLE FIX: FORCED BLACK */
        [data-testid="stSidebar"] h1 {{
            color: black !important;
        }}
        
        /* 3. CHAT MESSAGE TEXT COLOR: Forced Black (against the near-white background) */
        /* 4. CHAT MESSAGE BOX BACKGROUND: White with 0.9 opacity */
        .stChatMessage {{
            background: rgba(255, 255, 255, 0.9) !important; 
            border-radius: 10px;
            padding: 10px; 
            margin-bottom: 0.5rem; 
            color: black !important; 
        }}
        
        /* Main chat area overlay (Low opacity black for background) */
        .st-emotion-cache-1c9vslv {{ 
            background: rgba(0, 0, 0, 0.9); 
            border-radius: 10px;
        }}

        /* --- Input and Spacing Styles (Kept for consistency) --- */
        
        /* Input box width reduction */
        .stChatInput {{
            max-width: 500px; 
            margin: 0 auto; 
        }}

        /* Reduction of vertical space/height for the chat input and removal of useless padding */
        .stChatInput > div:first-child {{
            min-height: 2.5rem; 
            padding-top: 0.25rem; 
            padding-bottom: 0.25rem; 
        }}

        /* Remove excess bottom margin from the chat input area */
        [data-testid="stForm"] {{
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }}
        
        /* Remove footer-related padding/margins if present */
        .st-emotion-cache-1629p8f {{ 
            padding-bottom: 0.5rem; 
        }}

        /* Reduce margin above the chat input */
        .stForm {{
            margin-top: 0.5rem; 
        }}

        /* Center the input area wrapper */
        footer ~ div > div:last-child > div:last-child {{
            display: flex;
            justify-content: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    # 0. Set the background image and other styles
    set_styles(BACKGROUND_IMAGE_URL)
    
    # 1. Get sidebar context
    personality_key, display_name, fundamentals, mood = sidebar_options()

    # Dynamic Title 
    st.title(f"Chatting with {display_name}") 
    
    # 2. Initialize history and mood state
    initialize_session_state(personality_key)
    
    history_key = f"messages_{personality_key}"
    current_messages = st.session_state[history_key]

    # 3. Get the system instruction based on the full display name and current mood
    system_instruction = get_system_instruction(display_name, fundamentals, mood)

    # 4. Display chat messages
    llm_avatar_url = PERSONALITY_IMAGES.get(personality_key)
    
    for message in current_messages:
        role = message["role"]
        
        avatar = llm_avatar_url if role == "assistant" else "user" 
        
        if role in ["user", "assistant"]:
            with st.chat_message(role, avatar=avatar):
                st.write(message["content"])

    # 5. Chat input
    if prompt := st.chat_input(f"Send a message to {display_name}..."):
        
        # Append the user message to history immediately.
        current_messages.append({"role": "user", "content": prompt})
        
        # Display the user message right away so it shows up before the LLM thinks
        with st.chat_message("user"):
            st.write(prompt)
        
        # Call function to get response (new_mood will just be the static current mood)
        chat_response, new_mood = get_gemini_response(
            system_instruction, 
            current_messages[:-1], 
            prompt,
            mood 
        )
        
        # Display assistant response
        with st.chat_message("assistant", avatar=llm_avatar_url):
            st.write(chat_response)
        
        # Append ONLY the extracted chat text to history
        current_messages.append({"role": "assistant", "content": chat_response})

if __name__ == "__main__":
    main()