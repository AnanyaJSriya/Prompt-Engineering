import streamlit as st
import speech_recognition as sr
import time
import anthropic
import os

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
    st.session_state.recording = False
    st.session_state.recording_start_time = None

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

def transcribe_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... (Double-click stopped, now recording)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        try:
            audio = recognizer.listen(source, timeout=300, phrase_time_limit=300)
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "TIMEOUT"
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError:
            return "Could not request results"
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
    
    # Microphone instructions
    st.info("🎤 Double-click the button below to start speaking. Click once when done (max 5 minutes).")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🎤 Speak", key=f"mic_{st.session_state.round}"):
            if not st.session_state.recording:
                st.session_state.recording = True
                st.session_state.recording_start_time = time.time()
                st.rerun()
            else:
                st.session_state.recording = False
                with st.spinner("Processing your speech..."):
                    user_speech = transcribe_audio()
                    
                    if user_speech and user_speech not in ["TIMEOUT", "Could not understand audio", "Could not request results"]:
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
                        
                        if st.session_state.round >= 5:
                            st.session_state.stage = 'summary'
                        
                        st.rerun()
                    else:
                        st.error("Could not capture audio. Please try again.")
    
    with col2:
        if st.session_state.recording and st.session_state.recording_start_time:
            elapsed = time.time() - st.session_state.recording_start_time
            remaining = 300 - elapsed
            
            if remaining <= 60 and remaining > 0:
                st.warning(f"⏰ Reminder: {int(remaining)} seconds remaining!")
            elif remaining <= 0:
                st.error("⏰ Time's up! Click the microphone to submit.")
                st.session_state.recording = False
            else:
                st.info(f"⏱️ Recording... {int(remaining)} seconds remaining")

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
        st.session_state.recording = False
        st.session_state.recording_start_time = None
        st.rerun()
