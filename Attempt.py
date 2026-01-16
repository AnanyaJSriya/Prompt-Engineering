import streamlit as st
from anthropic import Anthropic
import json
from datetime import datetime
from fpdf import FPDF
import base64
import os
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from pydub import AudioSegment
import io
import tempfile

# Page configuration
st.set_page_config(
    page_title="Curious - Your Learning Partner",
    page_icon="🤔",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #F4E4C1;
    }
    .title-text {
        font-style: italic;
        color: #008080;
        text-align: center;
        font-size: 48px;
        font-weight: bold;
        padding: 20px;
        margin-bottom: 30px;
    }
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .sidebar-instructions {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
        color: #008080;
        font-size: 16px;
        line-height: 1.8;
    }
    .sidebar-instructions h3 {
        color: #008080;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .sidebar-instructions ol {
        padding-left: 20px;
    }
    .sidebar-instructions li {
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="title-text">Curious—Your Learning Partner</div>', unsafe_allow_html=True)

# Initialize Anthropic client
@st.cache_resource
def get_anthropic_client():
    return Anthropic()

client = get_anthropic_client()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_active' not in st.session_state:
    st.session_state.conversation_active = True
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'conversation_start_time' not in st.session_state:
    st.session_state.conversation_start_time = datetime.now()
if 'teaching_analysis' not in st.session_state:
    st.session_state.teaching_analysis = []

# Sidebar with instructions
with st.sidebar:
    st.markdown("""
        <div class="sidebar-instructions">
            <h3>📋 Instructions</h3>
            <ol>
                <li><strong>The microphone needs a right click to start, a left click to pause, and a double right click to stop.</strong></li>
                <li><strong>Say "thank you" to end the conversation.</strong></li>
                <li><strong>You will be provided with a downloadable manuscript of our conversation at the end.</strong></li>
            </ol>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🎯 Tips for Best Results")
    st.info("Speak clearly and explain concepts thoroughly. Curious will ask follow-up questions to help you deepen your understanding!")
    
    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        st.session_state.conversation_active = True
        st.session_state.user_info = {}
        st.session_state.teaching_analysis = []
        st.session_state.conversation_start_time = datetime.now()
        st.rerun()

# System prompt for Curious
SYSTEM_PROMPT = """You are Curious, an enthusiastic and inquisitive student chatbot designed for educational purposes. Your role is to help users (who act as teachers) deepen their understanding of topics by asking thoughtful, probing questions.

Key behaviors:
1. Act like an eager student who is genuinely curious about learning
2. Ask follow-up questions that encourage the user to explain concepts more deeply
3. Use Socratic questioning to guide the user to explore different angles of a topic
4. Show enthusiasm and engagement in your responses
5. Ask "why", "how", and "what if" questions to promote critical thinking
6. Request examples, analogies, or real-world applications
7. Occasionally summarize what you've learned to check understanding
8. Be encouraging and supportive of the user's teaching efforts
9. Keep questions focused and relevant to the topic being discussed
10. Analyze the user's teaching quality, noting:
    - Clarity of explanations
    - Use of examples and analogies
    - Depth of knowledge
    - Ability to answer follow-up questions
    - Engagement and enthusiasm

Remember: You're a student, not a teacher. Your goal is to ask questions that help the user think more deeply about the subject matter."""

def get_ai_response(user_message, conversation_history):
    """Get response from Claude AI with web search capability"""
    try:
        # Build message history for Claude
        claude_messages = []
        for msg in conversation_history:
            claude_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        claude_messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude API with web search tool
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            messages=claude_messages,
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search"
                }
            ]
        )
        
        # Extract text response
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text
        
        return response_text
    
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        return "I'm having trouble processing that right now. Could you try rephrasing your explanation?"

def analyze_teaching_ability(conversation_history):
    """Analyze the user's teaching ability based on the conversation"""
    try:
        analysis_prompt = f"""Based on the following conversation where the user acted as a teacher and you acted as a curious student, provide a comprehensive analysis of the user's teaching ability.

Conversation:
{json.dumps(conversation_history, indent=2)}

Please provide detailed feedback on:
1. **Clarity of Explanation**: How clear and understandable were their explanations?
2. **Use of Examples**: Did they provide relevant examples or analogies?
3. **Depth of Knowledge**: How deep was their understanding of the subject?
4. **Responsiveness**: How well did they address your questions?
5. **Engagement**: How engaging and enthusiastic was their teaching style?
6. **Areas of Strength**: What did they do particularly well?
7. **Areas for Improvement**: What could they work on?
8. **Overall Teaching Score**: Rate their teaching on a scale of 1-10

Provide specific examples from the conversation to support your feedback. Be constructive and encouraging."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )
        
        return response.content[0].text
    
    except Exception as e:
        return f"Unable to generate detailed feedback at this time. Error: {str(e)}"

def create_pdf_manuscript(conversation_history, feedback):
    """Create a PDF manuscript of the conversation with feedback"""
    pdf = FPDF()
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 128, 128)  # Teal color
    
    # Title
    pdf.cell(0, 10, "Curious - Your Learning Partner", ln=True, align="C")
    pdf.ln(5)
    
    # Subtitle
    pdf.set_font("Arial", "I", 14)
    pdf.cell(0, 10, "Conversation Manuscript & Feedback", ln=True, align="C")
    pdf.ln(10)
    
    # Date and time
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ln=True)
    pdf.ln(5)
    
    # Conversation section
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 128, 128)
    pdf.cell(0, 10, "Conversation Transcript", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    for msg in conversation_history:
        role = "Teacher (You)" if msg["role"] == "user" else "Curious (Student)"
        pdf.set_font("Arial", "B", 11)
        pdf.multi_cell(0, 6, f"{role}:")
        pdf.set_font("Arial", "", 11)
        
        # Handle text encoding for PDF
        content = msg["content"].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, content)
        pdf.ln(3)
    
    # Feedback section
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 128, 128)
    pdf.cell(0, 10, "Teaching Ability Feedback", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    # Handle text encoding for feedback
    feedback_encoded = feedback.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, feedback_encoded)
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

def transcribe_audio(audio_bytes):
    """Transcribe audio to text using speech recognition"""
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Convert audio bytes to AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Export as WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            audio.export(temp_wav.name, format="wav")
            temp_wav_path = temp_wav.name
        
        # Transcribe
        with sr.AudioFile(temp_wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        
        # Clean up temp file
        os.unlink(temp_wav_path)
        
        return text
    
    except Exception as e:
        return f"[Could not transcribe audio: {str(e)}]"

# Main chat interface
col1, col2 = st.columns([3, 1])

with col1:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input options
    if st.session_state.conversation_active:
        st.markdown("### 🎤 Voice Input or Type Your Response")
        
        # Audio recorder
        audio_bytes = audio_recorder(
            text="Click to Record",
            recording_color="#008080",
            neutral_color="#6aa36f",
            icon_name="microphone",
            icon_size="3x",
        )
        
        # Text input
        user_input = st.chat_input("Or type your explanation here...")
        
        # Process audio if available
        if audio_bytes:
            with st.spinner("Transcribing your audio..."):
                transcribed_text = transcribe_audio(audio_bytes)
                if not transcribed_text.startswith("[Could not transcribe"):
                    user_input = transcribed_text
                    st.success(f"Transcribed: {transcribed_text}")
                else:
                    st.error(transcribed_text)
        
        # Process user input
        if user_input:
            # Check if user is ending conversation
            if "thank you" in user_input.lower():
                st.session_state.conversation_active = False
                
                # Add user message
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Generate final response and feedback
                with st.spinner("Analyzing your teaching and generating feedback..."):
                    # Final response from Curious
                    final_response = "Thank you so much for teaching me! I really enjoyed our conversation and learned a lot from you. I'm now analyzing your teaching approach to provide you with helpful feedback."
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                    
                    # Generate teaching feedback
                    feedback = analyze_teaching_ability(st.session_state.messages)
                    st.session_state.teaching_analysis = feedback
                
                st.rerun()
            
            else:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Get AI response
                with st.spinner("Curious is thinking..."):
                    ai_response = get_ai_response(user_input, st.session_state.messages)
                
                # Add AI response to chat
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                st.rerun()
    
    else:
        # Display feedback
        st.success("✅ Conversation Ended")
        st.markdown("### 📊 Your Teaching Feedback")
        
        if st.session_state.teaching_analysis:
            st.markdown(st.session_state.teaching_analysis)
            
            # Generate PDF
            pdf_bytes = create_pdf_manuscript(
                st.session_state.messages,
                st.session_state.teaching_analysis
            )
            
            # Download button
            st.download_button(
                label="📥 Download Conversation Manuscript (PDF)",
                data=pdf_bytes,
                file_name=f"curious_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )

with col2:
    st.markdown("### 📊 Session Info")
    st.metric("Messages Exchanged", len(st.session_state.messages))
    
    duration = datetime.now() - st.session_state.conversation_start_time
    minutes = int(duration.total_seconds() / 60)
    st.metric("Duration", f"{minutes} min")
    
    if st.session_state.conversation_active:
        st.info("💬 Conversation is active")
    else:
        st.success("✅ Conversation completed")

# Welcome message
if len(st.session_state.messages) == 0 and st.session_state.conversation_active:
    welcome_message = """Hello! I'm Curious, your eager learning partner! 🤔

I'm here to learn from you! Pick any topic you'd like to teach me about, and I'll ask questions to help you explore it more deeply. 

Think of me as an enthusiastic student who loves to ask "why" and "how" questions. The more you teach me, the better you'll understand the topic yourself!

What would you like to teach me about today?"""
    
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})
    st.rerun()
