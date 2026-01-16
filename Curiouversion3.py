import streamlit as st
import time
import anthropic
import os
import io
import speech_recognition as sr
from pydub import AudioSegment

# Page config
st.set_page_config(page_title="Curious - Your Personal Student", layout="centered")

# Initialize session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'name'
    st.session_state.user_name = ''
    st.session_state.topic = ''
    st.session_state.round = 0
    st.session_state.conversation_history = []
    st.session_state.learned_points = []
    st.session_state.audio_data = None

# Header
st.markdown("<h1 style='text-align: center;'>🤖 Curious</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Your personal student</h3>", unsafe_allow_html=True)
st.markdown("---")

# Check for API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error("⚠️ ANTHROPIC_API_KEY not found in environment variables!")
    st.info("Please add your Anthropic API key to Streamlit secrets or environment variables.")
    st.stop()

# Initialize Anthropic client
try:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
except Exception as e:
    st.error(f"Failed to initialize Anthropic client: {str(e)}")
    st.stop()

def get_ai_response(prompt, conversation_context=""):
    """Get response from Claude AI"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": f"{conversation_context}\n\n{prompt}"}
            ]
        )
        
        full_response = ""
        for block in response.content:
            if block.type == "text":
                full_response += block.text
        
        return full_response
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return "I'm having trouble processing that. Can you explain more?"

def convert_to_wav(audio_bytes, input_format):
    """Convert audio to WAV format for speech recognition"""
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=input_format)
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        return wav_io
    except Exception as e:
        st.error(f"Audio conversion error: {str(e)}")
        return None

def transcribe_audio(audio_bytes, file_extension):
    """Transcribe audio to text using Google Speech Recognition"""
    try:
        # Convert to WAV if needed
        if file_extension.lower() != 'wav':
            audio_format = file_extension.lower().replace('.', '')
            wav_io = convert_to_wav(audio_bytes, audio_format)
            if wav_io is None:
                return "Failed to convert audio format"
        else:
            wav_io = io.BytesIO(audio_bytes)
        
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(wav_io) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            # Try to recognize speech
            text = recognizer.recognize_google(audio_data)
            return text
            
    except sr.UnknownValueError:
        return "Could not understand the audio. Please speak clearly and try again."
    except sr.RequestError as e:
        return f"Speech recognition service error: {str(e)}"
    except Exception as e:
        return f"Transcription error: {str(e)}"

# Stage: Name Input
if st.session_state.stage == 'name':
    st.write("Welcome to Curious! I'm excited to learn from you.")
    name_input = st.text_input("Please type your name:", key="name_input")
    if st.button("Submit Name"):
        if name_input:
            st.session_state.user_name = name_input
            st.session_state.stage = 'greeting'
            st.session_state.conversation_history.append(f"User name: {name_input}")
            st.rerun()
        else:
            st.warning("Please enter your name to continue.")

# Stage: Greeting
elif st.session_state.stage == 'greeting':
    st.write(f"**Curious:** Hello, Teacher {st.session_state.user_name}! What are we going to learn today?")
    st.session_state.stage = 'topic'
    st.rerun()

# Stage: Topic Input
elif st.session_state.stage == 'topic':
    st.write(f"**Curious:** Hello, Teacher {st.session_state.user_name}! What are we going to learn today?")
    topic_input = st.text_input("Type the topic:", key="topic_input")
    if st.button("Submit Topic"):
        if topic_input:
            st.session_state.topic = topic_input
            st.session_state.stage = 'curious'
            st.session_state.conversation_history.append(f"Topic: {topic_input}")
            st.rerun()
        else:
            st.warning("Please enter a topic to continue.")

# Stage: Curious Response
elif st.session_state.stage == 'curious':
    st.write(f"**Curious:** Hello, Teacher {st.session_state.user_name}! What are we going to learn today?")
    st.write(f"**You:** {st.session_state.topic}")
    st.write(f"**Curious:** I am curious to learn about {st.session_state.topic}!")
    st.session_state.stage = 'learning'
    time.sleep(2)
    st.rerun()

# Stage: Learning Rounds
elif st.session_state.stage == 'learning':
    # Display conversation history
    st.write(f"**Topic:** {st.session_state.topic}")
    st.write(f"**Round:** {st.session_state.round + 1}/5")
    st.markdown("---")
    
    for msg in st.session_state.conversation_history[-10:]:
        if msg.startswith("User name:") or msg.startswith("Topic:"):
            continue
        st.write(msg)
    
    st.markdown("---")
    
    # Audio input with file uploader
    st.info("🎤 Upload your audio explanation below")
    st.caption("Supported formats: WAV, MP3, OGG, M4A, FLAC")
    
    audio_file = st.file_uploader(
        "Choose an audio file",
        type=['wav', 'mp3', 'ogg', 'm4a', 'flac'],
        key=f"audio_upload_{st.session_state.round}"
    )
    
    if audio_file is not None:
        st.session_state.audio_data = audio_file
        st.audio(audio_file, format=f'audio/{audio_file.name.split(".")[-1]}')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        submit_button = st.button("Submit Audio", key=f"submit_{st.session_state.round}", use_container_width=True)
    
    with col2:
        if st.button("Skip to Summary", key=f"skip_{st.session_state.round}", use_container_width=True):
            st.session_state.stage = 'summary'
            st.rerun()
    
    if submit_button:
        if st.session_state.audio_data is not None:
            with st.spinner("🎧 Processing your speech..."):
                audio_bytes = st.session_state.audio_data.getvalue()
                file_extension = st.session_state.audio_data.name.split('.')[-1]
                
                user_speech = transcribe_audio(audio_bytes, file_extension)
                
                if user_speech and not user_speech.startswith("Could not") and not user_speech.startswith("Speech recognition") and not user_speech.startswith("Transcription error"):
                    st.success("✅ Audio transcribed successfully!")
                    st.info(f"**Transcription:** {user_speech}")
                    
                    st.session_state.conversation_history.append(f"**You:** {user_speech}")
                    
                    # Get AI response
                    with st.spinner("🤔 Curious is thinking..."):
                        context = f"You are Curious, an enthusiastic student learning about {st.session_state.topic}. The teacher just explained: {user_speech}. Ask ONE specific, inquisitive question to deepen your understanding. Keep it concise, curious, and relevant."
                        
                        ai_question = get_ai_response(
                            f"Based on this explanation about {st.session_state.topic}, ask one specific inquisitive question to deepen understanding: {user_speech}",
                            context
                        )
                        
                        st.session_state.conversation_history.append(f"**Curious:** {ai_question}")
                        st.session_state.learned_points.append(user_speech)
                        st.session_state.round += 1
                        st.session_state.audio_data = None
                        
                        if st.session_state.round >= 5:
                            st.session_state.stage = 'summary'
                        
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error(f"❌ {user_speech}")
                    st.info("Please try recording again with clearer audio.")
        else:
            st.warning("⚠️ Please upload an audio file first!")

# Stage: Summary
elif st.session_state.stage == 'summary':
    st.success("🎉 Learning Session Complete!")
    st.write(f"**Curious:** Thank you so much, Teacher {st.session_state.user_name}!")
    st.write("Here's what I learned today:")
    st.markdown("---")
    
    # Generate summary
    if st.session_state.learned_points:
        with st.spinner("📝 Generating learning summary..."):
            summary_prompt = f"Summarize the following learning points about {st.session_state.topic} into 5-7 concise, well-organized bullet points. Focus on the key concepts and insights:\n\n" + "\n\n".join(st.session_state.learned_points)
            summary = get_ai_response(summary_prompt)
            st.write(summary)
    else:
        st.write("No learning points were recorded in this session.")
    
    st.markdown("---")
    
    if st.button("🔄 Start New Session", use_container_width=True):
        # Reset session
        st.session_state.stage = 'name'
        st.session_state.user_name = ''
        st.session_state.topic = ''
        st.session_state.round = 0
        st.session_state.conversation_history = []
        st.session_state.learned_points = []
        st.session_state.audio_data = None
        st.rerun()
