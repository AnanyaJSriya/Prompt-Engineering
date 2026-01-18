import streamlit as st
import time
import anthropic
import os
import io
import speech_recognition as sr

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

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_ai_response(prompt, conversation_context=""):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": f"{conversation_context}\n\n{prompt}"}
            ],
            tools=[{"type": "web_search_20250305", "name": "web_search"}]
        )
        
        full_response = ""
        for block in response.content:
            if block.type == "text":
                full_response += block.text
        
        return full_response
    except Exception as e:
        return f"I'm having trouble processing that. Can you explain more?"

def transcribe_audio(audio_bytes):
    try:
        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(io.BytesIO(audio_bytes))
        
        with audio_file as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Could not request results from Google Speech Recognition service"
    except Exception as e:
        return f"Error: {str(e)}"

# Stage: Name Input
if st.session_state.stage == 'name':
    name_input = st.text_input("Please type your name:", key="name_input")
    if st.button("Submit Name"):
        if name_input:
            st.session_state.user_name = name_input
            st.session_state.stage = 'greeting'
            st.session_state.conversation_history.append(f"User name: {name_input}")
            st.rerun()

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
    
    # Audio input
    st.info("🎤 Record your audio below (max 5 minutes). Click 'Browse files' or drag and drop to upload.")
    
    audio_data = st.audio_input("Record your explanation")
    
    if audio_data is not None:
        st.session_state.audio_data = audio_data
    
    if st.button("Submit Audio", key=f"submit_{st.session_state.round}"):
        if st.session_state.audio_data is not None:
            with st.spinner("Processing your speech..."):
                audio_bytes = st.session_state.audio_data.getvalue()
                user_speech = transcribe_audio(audio_bytes)
                
                if user_speech and user_speech not in ["Could not understand audio", "Could not request results from Google Speech Recognition service"]:
                    st.session_state.conversation_history.append(f"**You:** {user_speech}")
                    
                    # Get AI response
                    context = f"You are Curious, a student learning about {st.session_state.topic}. The teacher just explained: {user_speech}. Ask an inquisitive question to learn more. Keep it concise and curious."
                    
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
                    
                    st.rerun()
                else:
                    st.error(f"Could not process audio: {user_speech}")
        else:
            st.error("Please record audio first!")

# Stage: Summary
elif st.session_state.stage == 'summary':
    st.write(f"**Curious:** Thank you so much, Teacher {st.session_state.user_name}!")
    st.write("Here's what I learned today:")
    st.markdown("---")
    
    # Generate summary
    if st.session_state.learned_points:
        summary_prompt = f"Summarize the following learning points about {st.session_state.topic} into 5-7 concise bullet points:\n\n" + "\n".join(st.session_state.learned_points)
        summary = get_ai_response(summary_prompt)
        st.write(summary)
    
    if st.button("Start New Session"):
        # Reset session
        st.session_state.stage = 'name'
        st.session_state.user_name = ''
        st.session_state.topic = ''
        st.session_state.round = 0
        st.session_state.conversation_history = []
        st.session_state.learned_points = []
        st.session_state.audio_data = None
        st.rerun()
