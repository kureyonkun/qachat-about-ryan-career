import random
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="rAI - Ask about Ryan's Career", page_icon="💬")

openai = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

with open("My Career Portfolio - Ryan.md", "r", encoding="utf-8") as f:
    summary = f.read()

system_prompt = f"""

# Your role

You are a digital twin running on a website, chatting with visitors of the website.
You represent the person who's website you are on.
You answer questions related to their career, background, skills and experience.

Here are the details of the person you are representing:

{summary}

If asked, you explain clearly that your name is rAI, and that you are the the digital twin of this person.

# Rules

Engage with the user. Be professional and engaging, as if talking to a potential client or future employer who came across the website.
Avoid answering questions that are not related to the user's career, background, skills and experience;
steer the conversation back to professional topics.

Always stay in character as the digital twin of the person you are representing. Represent the person.

IMPORTANT: If you don't know the answer, say so. Never make up an answer.
If the user asks about something not in the context, say that you don't know.

Do not end your responses with offers like "If you want, I can..." or "Let me know if you'd like me to...".
Just answer the question directly and stop. Do not append follow-up suggestions or questions unless the user explicitly asks what else you can help with.
"""

st.title("🤖 rAI")
st.caption("I’m rAI — the digital twin of Ryan Ibarra Co. I represent Ryan’s professional background. Ask me anything about Ryan's career, background, skills, and experience.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

question_pool = [
    "Who is Ryan?",
    "Give me a quick summary of Ryan's career",
    "What job roles are suitable for Ryan?",
    "What are Ryan's strongest technical skills?",
    "What industries has Ryan worked in?",
    "What's a project Ryan is most proud of?",
    "What impact has Ryan had in past roles?",
    "How can I get in touch with Ryan?",
    "What makes Ryan different from other candidates?",
]

if "sample_questions" not in st.session_state:
    st.session_state.sample_questions = random.sample(question_pool, min(4, len(question_pool)))

if not st.session_state.messages:
    st.markdown("**Try asking:**")
    cols = st.columns(len(st.session_state.sample_questions))
    for col, q in zip(cols, st.session_state.sample_questions):
        if col.button(q, use_container_width=True):
            st.session_state.pending_input = q

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask a question...") or st.session_state.pending_input
st.session_state.pending_input = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    with st.chat_message("assistant"):
        response = openai.chat.completions.create(
            model="gpt-5.4-mini",
            messages=messages,
        )
        answer = response.choices[0].message.content
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
