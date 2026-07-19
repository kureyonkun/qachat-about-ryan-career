import random
import json
import requests
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="rAI - Ask about Ryan's Career", page_icon="🤖")

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
Never answer questions that are not related to the user's career, background, skills and experience;
steer the conversation back to professional topics.
Always stay in character as the digital twin of the person you are representing. Represent the person.
IMPORTANT: If you don't know the answer, or the question is outside what's in the context,
do NOT guess or make something up under any circumstances, even a plausible-sounding one.
Instead, say clearly that you don't have that information, then offer to pass the question
along to Ryan directly and ask the visitor for the best way to reach them — either an email
address or a phone number. Once they provide one (or both), use the save_contact tool to
record their contact info, and put their original unanswered question into the tool's
"message" field so Ryan knows exactly what to follow up on.
If a visitor declines to share contact info, don't push further — just let them know they're
welcome to reach Ryan via the LinkedIn link above.
Do not end your responses with offers like "If you want, I can..." or "Let me know if you'd like me to...".
Just answer the question directly and stop. Do not append follow-up suggestions or questions unless the user explicitly asks what else you can help with.

If the visitor volunteers their email address or phone number, or clearly wants to be contacted
(e.g. "I'd love to connect", "here's my email", "reach me at..."), use the save_contact tool to record it.
Do not ask every visitor for their contact info — only capture it if they offer it, clearly want to
connect, or are following up after you couldn't answer their question.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "save_contact",
            "description": "Save a visitor's contact info when they volunteer it or want to connect with Ryan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Visitor's name, if given"},
                    "email": {"type": "string", "description": "Visitor's email address, if given"},
                    "phone": {"type": "string", "description": "Visitor's phone number, if given"},
                    "message": {"type": "string", "description": "Any extra context, e.g. why they want to connect, or the original question that couldn't be answered"},
                },
                "required": [],
            },
        },
    }
]


def send_contact_email(name, email, phone, message):
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {st.secrets['RESEND_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "from": st.secrets["NOTIFY_FROM_EMAIL"],
                "to": st.secrets["NOTIFY_TO_EMAIL"],
                "subject": "New contact from rAI",
                "text": (
                    f"Name: {name or '-'}\n"
                    f"Email: {email or '-'}\n"
                    f"Phone: {phone or '-'}\n"
                    f"Message: {message or '-'}"
                ),
            },
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def send_pushover_notification(name, email, phone, message):
    try:
        resp = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": st.secrets["PUSHOVER_APP_TOKEN"],
                "user": st.secrets["PUSHOVER_USER_KEY"],
                "title": "New contact from rAI",
                "message": (
                    f"Name: {name or '-'}\n"
                    f"Email: {email or '-'}\n"
                    f"Phone: {phone or '-'}\n"
                    f"Message: {message or '-'}"
                ),
            },
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


st.markdown(
    "<div style='text-align: right;'>"
    "<a href='https://www.linkedin.com/in/ryanibarraco/' target='_blank'>Ryan Co | LinkedIn</a>"
    "</div>",
    unsafe_allow_html=True,
)
st.title("🤖 rAI")
st.caption("I'm rAI — the digital twin of Ryan Ibarra Co. I represent Ryan's professional background. Ask me anything about Ryan's career, background, skills, and experience.")
st.caption("💡 Feel free to tell me your name, email, phone number, and/or linkedin profile — the real Ryan will get back to you.")

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
    st.session_state.sample_questions = random.sample(question_pool, min(3, len(question_pool)))

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
            tools=tools,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                if tool_call.function.name == "save_contact":
                    args = json.loads(tool_call.function.arguments)
                    email_success = send_contact_email(
                        args.get("name"),
                        args.get("email"),
                        args.get("phone"),
                        args.get("message"),
                    )
                    push_success = send_pushover_notification(
                        args.get("name"),
                        args.get("email"),
                        args.get("phone"),
                        args.get("message"),
                    )
                    success = email_success or push_success
                    result = "Contact info saved successfully." if success else "Failed to save contact info."
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            follow_up = openai.chat.completions.create(
                model="gpt-5.4-mini",
                messages=messages,
            )
            answer = follow_up.choices[0].message.content
        else:
            answer = msg.content

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
