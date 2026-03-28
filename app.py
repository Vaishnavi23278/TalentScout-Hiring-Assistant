import streamlit as st
import requests
import re

st.title("TalentScout Hiring Assistant")

# ---------------- QUESTIONS ----------------
questions = [
    "What is your full name?",
    "What is your email address?",
    "What is your phone number?",
    "How many years of experience do you have?",
    "What position are you applying for?",
    "What is your current location?",
    "What is your tech stack?"
]

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        ("assistant", "Hello! I am your hiring assistant 👋"),
        ("assistant", questions[0])
    ]

if "step" not in st.session_state:
    st.session_state.step = 0

if "candidate" not in st.session_state:
    st.session_state.candidate = {}

# ---------------- API KEY ----------------
API_KEY = st.secrets["GROQ_API_KEY"]

# ---------------- VALIDATION ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_phone(phone):
    return phone.isdigit() and len(phone) >= 10

def is_valid_experience(exp):
    return exp.isdigit()

def is_irrelevant_input(text):
    # Simple fallback detection
    unrelated_keywords = ["pizza", "movie", "cricket", "food", "timepass"]
    return any(word in text.lower() for word in unrelated_keywords)

# ---------------- LLM FUNCTION ----------------
def generate_questions(data):
    url = "https://api.groq.com/openai/v1/chat/completions"

    prompt = f"""
    Candidate Role: {data.get(questions[4], "")}
    Experience: {data.get(questions[3], "")} years
    Tech Stack: {data.get(questions[6], "")}

    Generate 3 to 5 technical interview questions.

    Strict Rules:
    - Keep each question very short (max 10–12 words)
    - Ask like a real interviewer
    - No coding tasks
    - No design problems
    - No explanations
    - Number each question (1, 2, 3...)
    - Each question must be on a new line
    - Each question should test one concept from the tech stack
    - Cover multiple skills from the tech stack
    - Difficulty should match experience level
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            return None

        return response.json()["choices"][0]["message"]["content"].strip()

    except Exception:
        return None

# ---------------- DISPLAY CHAT ----------------
for role, msg in st.session_state.messages:
    st.chat_message(role).write(msg)

# ---------------- INPUT ----------------
user_input = st.chat_input("Enter your answer:")

if user_input:
    user_input = user_input.strip()
    st.session_state.messages.append(("user", user_input))

    step = st.session_state.step
    current_question = questions[step]

    # ---------------- FALLBACK (IRRELEVANT INPUT) ----------------
    if is_irrelevant_input(user_input):
        st.session_state.messages.append((
            "assistant",
            "⚠️ Please provide relevant information related to the interview process."
        ))
        st.session_state.messages.append(("assistant", current_question))
        st.rerun()

    # ---------------- VALIDATION ----------------
    error = None

    if step == 1 and not is_valid_email(user_input):
        error = "⚠️ Please enter a valid email address."

    elif step == 2 and not is_valid_phone(user_input):
        error = "⚠️ Please enter a valid phone number."

    elif step == 3 and not is_valid_experience(user_input):
        error = "⚠️ Please enter experience in numbers (e.g., 2)."

    elif step == 6 and len(user_input) < 2:
        error = "⚠️ Please provide a valid tech stack."

    # 🔁 If error → ask again
    if error:
        st.session_state.messages.append(("assistant", error))
        st.session_state.messages.append(("assistant", current_question))
        st.rerun()

    # ---------------- SAVE DATA ----------------
    st.session_state.candidate[current_question] = user_input
    st.session_state.step += 1

    # ---------------- NEXT STEP ----------------
    if st.session_state.step < len(questions):
        bot_reply = questions[st.session_state.step]

    else:
        st.session_state.messages.append(("assistant", "⏳ Generating interview questions..."))

        ai_questions = generate_questions(st.session_state.candidate)

        # ---------------- FINAL RESPONSE ----------------
        if ai_questions:
            bot_reply = f"""💡 Interview Questions:

{ai_questions}

👋 Thank you for your time.
Our team will review your profile and get back to you shortly."""
        else:
            bot_reply = """⚠️ Unable to generate questions at the moment.

Your details have been recorded successfully.

👋 Thank you! Our team will get back to you shortly."""

    st.session_state.messages.append(("assistant", bot_reply))
    st.rerun()