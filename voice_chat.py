import streamlit as st
from openai import OpenAI
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Educational Voice Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAudio {
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4CAF50;
    }
    .timestamp {
        font-size: 0.75rem;
        color: #666;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
def get_openai_client():
    """Initialize OpenAI client with API key from secrets or environment"""
    api_key = None
    
    # Try to get API key from Streamlit secrets first
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except:
        # Fall back to environment variable
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        st.error("⚠️ OpenAI API key not found! Please add it to your secrets or environment variables.")
        st.stop()
    
    return OpenAI(api_key=api_key)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Sidebar
with st.sidebar:
    st.title("🎓 Educational Chatbot")
    st.markdown("---")
    
    # Settings
    st.subheader("Settings")
    
    model_choice = st.selectbox(
        "Select Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
        help="Choose the AI model for responses"
    )
    
    temperature = st.slider(
        "Creativity Level",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Higher values make responses more creative, lower values more focused"
    )
    
    max_tokens = st.slider(
        "Max Response Length",
        min_value=100,
        max_value=2000,
        value=500,
        step=100,
        help="Maximum length of AI responses"
    )
    
    st.markdown("---")
    
    # System prompt customization
    st.subheader("System Instructions")
    system_prompt = st.text_area(
        "Customize the chatbot's behavior",
        value="You are a helpful educational assistant. Explain concepts clearly and provide examples when helpful. Be encouraging and supportive to students.",
        height=150,
        help="Define how the chatbot should behave"
    )
    
    st.markdown("---")
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()
    
    # Conversation stats
    st.markdown("---")
    st.subheader("Statistics")
    st.metric("Messages", len(st.session_state.messages))
    
    # Instructions
    st.markdown("---")
    st.subheader("How to Use")
    st.markdown("""
    1. 🎤 **Click the microphone** to record your question
    2. 🗣️ **Speak clearly** into your device
    3. 📝 **Or type** your question in the text box
    4. ⏹️ **Stop recording** when done
    5. ✨ **Get instant** AI responses
    """)

# Main content
st.title("🎓 Educational Voice Chatbot")
st.markdown("Ask questions using your voice or text!")

# Initialize OpenAI client
client = get_openai_client()

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        timestamp = message.get("timestamp", "")
        
        if role == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>🧑 You:</strong>
                    <p>{content}</p>
                    <div class="timestamp">{timestamp}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistant:</strong>
                    <p>{content}</p>
                    <div class="timestamp">{timestamp}</div>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Input section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎤 Voice Input")
    audio_file = st.audio_input("Record your question")

with col2:
    st.subheader("⚙️ Audio Settings")
    st.info("Record in a quiet environment for best results")

# Text input as alternative
st.subheader("⌨️ Text Input")
text_input = st.text_area(
    "Or type your question here",
    placeholder="Enter your question...",
    height=100,
    key="text_input"
)

# Submit button
submit_button = st.button("📤 Submit", type="primary", use_container_width=True)

# Process input
def transcribe_audio(audio_data):
    """Transcribe audio using OpenAI Whisper"""
    try:
        # Save audio temporarily
        temp_audio_path = "/tmp/temp_audio.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_data.getbuffer())
        
        # Transcribe using Whisper
        with open(temp_audio_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="en"  # Can be changed or made dynamic
            )
        
        # Clean up
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        return transcript.text
    
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None

def get_ai_response(user_message):
    """Get response from OpenAI"""
    try:
        # Prepare conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in st.session_state.conversation_history:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Get response
        with st.spinner("🤔 Thinking..."):
            response = client.chat.completions.create(
                model=model_choice,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        assistant_message = response.choices[0].message.content
        
        # Update conversation history
        st.session_state.conversation_history.append({"role": "user", "content": user_message})
        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        return None

# Handle submission
if submit_button:
    user_message = None
    
    # Process audio input
    if audio_file is not None:
        with st.spinner("🎧 Transcribing your audio..."):
            transcribed_text = transcribe_audio(audio_file)
            if transcribed_text:
                user_message = transcribed_text
                st.success(f"✅ Transcribed: *{transcribed_text}*")
    
    # Fall back to text input if no audio
    if user_message is None and text_input.strip():
        user_message = text_input.strip()
    
    # Get AI response
    if user_message:
        timestamp = datetime.now().strftime("%I:%M %p")
        
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": timestamp
        })
        
        # Get and display AI response
        ai_response = get_ai_response(user_message)
        
        if ai_response:
            st.session_state.messages.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": timestamp
            })
        
        # Rerun to update chat display
        st.rerun()
    else:
        st.warning("⚠️ Please record audio or enter text before submitting.")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Powered by OpenAI Whisper & GPT | Built with Streamlit</p>
        <p style="font-size: 0.8rem;">Tip: Speak clearly and in a quiet environment for best transcription results</p>
    </div>
""", unsafe_allow_html=True)
