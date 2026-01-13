import streamlit as st

BOT_NAME = "Curious"

if "conversation_active" not in st.session_state:
    st.session_state.conversation_active = False

if "topic" not in st.session_state:
    st.session_state.topic = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

def curious_question_generator(topic):
    questions = [
        f"Why do you think {topic} is important?",
        f"Can you explain {topic} using a real-life example?",
        f"What challenges exist in understanding {topic}?",
        f"How would you teach {topic} to a beginner?",
        f"What future impact do you think {topic} will have?"
    ]
    return questions[len(st.session_state.messages) % len(questions)]

def generate_report(messages):
    report = (
        "Here is what I learned from our peer learning session:\n\n"
        "Through your explanations, I gained clarity on the topic and its real-world relevance. "
        "You broke down complex ideas into simpler components, which helped me understand the core concepts better. "
        "The examples you shared played a key role in connecting theory with practice. "
        "I also learned how different challenges affect this topic and how they can be addressed with thoughtful approaches. "
        "Your way of teaching highlighted not just factual understanding but also critical thinking. "
        "Overall, this learning session helped me develop curiosity, analytical thinking, and appreciation for structured explanation. "
        "Peer learning made the topic more engaging, interactive, and meaningful."
    )
    return report

st.title("🤖 Curious – Your Peer Learning Companion")

user_input = st.text_input("You (Teacher):")

if user_input == "Let’s Learn":
    st.session_state.conversation_active = True
    st.session_state.messages = []
    st.success("Curious is ready to learn! Please start teaching your topic.")

elif user_input == "Happy Learning":
    st.session_state.conversation_active = False
    st.success("Conversation ended. Thank you for peer learning!")

elif user_input == "What did you learn?" and st.session_state.conversation_active:
    report = generate_report(st.session_state.messages)
    st.markdown("### 📘 Curious's Learning Report")
    st.write(report)

elif st.session_state.conversation_active and user_input:
    st.session_state.messages.append(user_input)
    question = curious_question_generator(user_input)
    st.markdown(f"**{BOT_NAME}:** {question}")
