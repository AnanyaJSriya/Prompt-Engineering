import streamlit as st

BOT_NAME = "Curious"

# Initialize session state
if "conversation_active" not in st.session_state:
    st.session_state.conversation_active = False
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "question_count" not in st.session_state:
    st.session_state.question_count = 0

def curious_question_generator(topic, count):
    """Generate contextual questions based on conversation progress"""
    questions = [
        f"What inspired you to learn about {topic}?",
        f"Can you explain the key concepts of {topic} in simple terms?",
        f"What real-world example best illustrates {topic}?",
        f"What challenges or misconceptions exist around {topic}?",
        f"How would you teach {topic} to someone with no background?",
        f"What connections does {topic} have to other areas?",
        f"What future developments do you see for {topic}?",
        f"What aspect of {topic} do you find most fascinating?"
    ]
    if count < len(questions):
        return questions[count]
    else:
        return f"Is there anything else about {topic} you'd like to share?"

def generate_report(messages, topic):
    """Generate a report that references actual conversation content"""
    if not messages:
        return "No conversation to summarize yet."
    
    report = f"# 📘 Learning Report: {topic}\n\n"
    report += f"**Topic:** {topic}\n\n"
    report += f"**Number of exchanges:** {len(messages) // 2}\n\n"
    report += "## Key Points Discussed:\n\n"
    
    # Extract user responses (odd indices)
    for i, msg in enumerate(messages):
        if i % 2 == 1:  # User responses
            report += f"- {msg[:100]}{'...' if len(msg) > 100 else ''}\n"
    
    report += "\n## Reflection:\n\n"
    report += (
        "Through this peer learning session, I gained insights into your understanding of the topic. "
        "Your explanations helped break down complex ideas, and the examples you provided made the concepts "
        "more tangible. This interactive approach to learning encourages deeper thinking and better retention. "
        "Thank you for taking the time to teach me!"
    )
    
    return report

# UI Layout
st.title("🤖 Curious – Your Peer Learning Companion")
st.markdown("*Teach Curious about any topic, and it will ask questions to help deepen your understanding!*")

# Display conversation history
if st.session_state.messages:
    st.markdown("### 💬 Conversation History")
    for i, msg in enumerate(st.session_state.messages):
        if i % 2 == 0:  # Bot questions
            st.markdown(f"**{BOT_NAME}:** {msg}")
        else:  # User responses
            st.markdown(f"**You:** {msg}")
    st.markdown("---")

# Input area
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    user_input = st.text_input("Your message:", key="user_input", label_visibility="collapsed")

with col2:
    if st.button("Send"):
        if user_input:
            # Process the input
            if user_input.lower() == "let's learn":
                st.session_state.conversation_active = True
                st.session_state.messages = []
                st.session_state.question_count = 0
                st.session_state.topic = ""
                st.rerun()
            elif user_input.lower() == "happy learning":
                st.session_state.conversation_active = False
                st.success("Conversation ended. Thank you for peer learning!")
                st.rerun()
            elif user_input.lower() == "what did you learn?":
                if st.session_state.messages:
                    report = generate_report(st.session_state.messages, st.session_state.topic)
                    st.markdown(report)
                else:
                    st.warning("We haven't had a conversation yet!")
            elif st.session_state.conversation_active:
                # Set topic from first user message if not set
                if not st.session_state.topic:
                    st.session_state.topic = user_input
                
                # Add user response
                st.session_state.messages.append(user_input)
                
                # Generate and add bot question
                question = curious_question_generator(st.session_state.topic, st.session_state.question_count)
                st.session_state.messages.append(question)
                st.session_state.question_count += 1
                
                st.rerun()
            else:
                st.warning("Please type 'Let's Learn' to start a conversation!")

with col3:
    if st.button("Clear"):
        st.session_state.messages = []
        st.session_state.conversation_active = False
        st.session_state.topic = ""
        st.session_state.question_count = 0
        st.rerun()

# Instructions
with st.sidebar:
    st.markdown("## 📋 How to Use")
    st.markdown("""
    1. Type **"Let's Learn"** to start
    2. Enter the topic you want to teach
    3. Answer Curious's questions
    4. Type **"What did you learn?"** for a summary
    5. Type **"Happy Learning"** to end
    """)
    
    st.markdown("## 💡 Tips")
    st.markdown("""
    - Be detailed in your explanations
    - Use examples when possible
    - Don't worry about making mistakes - this is about learning!
    """)
