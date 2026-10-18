import datetime
import os

import streamlit as st
from groq import Groq

model = "openai/gpt-oss-120b"
appTitle = "Tutor Atelier"
subjectOptions = [
    "General",
    "Mathematics",
    "Physics",
    "Chemistry",
    "Biology",
    "Computer Science",
    "Economics",
    "Statistics",
    "History",
    "Literature",
]
levelOptions = ["High school", "Undergraduate", "Graduate", "Self-taught adult"]
styleOptions = ["Socratic", "Step-by-step", "Concise", "Worked examples"]
starterPrompts = [
    "Explain eigenvalues with an intuitive picture",
    "Walk me through integration by parts step by step",
    "Quiz me on Bayes' theorem",
]

cssText = """
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,500;1,6..72,400&family=IBM+Plex+Sans:wght@400;500&family=JetBrains+Mono:wght@400&display=swap');

:root {
  --ink: #0c1017;
  --deep: #090c12;
  --panel: #141b26;
  --line: #263346;
  --paper: #ebe3d0;
  --muted: #8792a4;
  --brass: #d9a45b;
  --teal: #63b5a6;
}

.stApp {
  background:
    radial-gradient(1200px 600px at 88% -12%, rgba(217, 164, 91, 0.10), transparent 60%),
    radial-gradient(900px 500px at -12% 112%, rgba(99, 181, 166, 0.08), transparent 55%),
    var(--ink);
  color: var(--paper);
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}

[data-testid="stHeader"] { background: transparent; }

[data-testid="stSidebar"] {
  background: var(--deep);
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] h2 {
  font-family: 'Newsreader', Georgia, serif;
  font-weight: 400;
  color: var(--paper);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stCaption {
  color: var(--muted);
}

.block-container {
  padding-top: 2.5rem;
  max-width: 880px;
}

.heroTitle {
  font-family: 'Newsreader', Georgia, serif;
  font-weight: 300;
  font-size: clamp(2.6rem, 6vw, 4.2rem);
  line-height: 1.02;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--paper);
  animation: riseIn 900ms cubic-bezier(.2, .7, .2, 1) both;
}

.heroLead {
  font-family: 'Newsreader', Georgia, serif;
  font-style: italic;
  font-size: 1.2rem;
  line-height: 1.5;
  color: var(--muted);
  max-width: 38ch;
  margin: 0.9rem 0 0;
  animation: riseIn 900ms 120ms cubic-bezier(.2, .7, .2, 1) both;
}

.heroRule {
  height: 1px;
  background: linear-gradient(90deg, var(--brass), transparent 70%);
  margin: 1.8rem 0 2rem;
}

@keyframes riseIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}

[data-testid="stChatMessage"] {
  background: transparent;
  border-left: 1px solid var(--line);
  padding: 0.4rem 0 0.4rem 1.2rem;
  margin: 1.1rem 0;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  border-left: 2px solid var(--brass);
  background: rgba(217, 164, 91, 0.05);
  margin-left: 12%;
  padding: 0.8rem 1.1rem;
  border-radius: 2px;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
  border-left: 2px solid var(--teal);
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
  line-height: 1.7;
  font-size: 1.02rem;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3 {
  font-family: 'Newsreader', Georgia, serif;
  font-weight: 500;
  color: var(--paper);
}

code, pre {
  font-family: 'JetBrains Mono', ui-monospace, monospace !important;
}

pre {
  background: var(--deep) !important;
  border: 1px solid var(--line);
  border-radius: 2px;
}

[data-testid="stChatInput"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 2px;
}

[data-testid="stChatInput"]:focus-within {
  border-color: var(--brass);
  box-shadow: 0 0 0 1px var(--brass);
}

.stButton > button,
.stDownloadButton > button {
  background: transparent;
  color: var(--brass);
  border: 1px solid var(--brass);
  border-radius: 2px;
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: background 200ms, color 200ms;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  background: rgba(217, 164, 91, 0.12);
  color: var(--paper);
  border-color: var(--brass);
}

.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible {
  outline: 2px solid var(--teal);
  outline-offset: 2px;
}

.stButton > button p {
  color: inherit;
  text-align: left;
  line-height: 1.4;
}

.stSelectbox div[data-baseweb="select"] > div,
.stTextInput input {
  background: var(--panel) !important;
  border-color: var(--line) !important;
  border-radius: 2px !important;
}

[data-testid="stSlider"] div[role="slider"] {
  background: var(--brass) !important;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
  }
}
"""


def currentTimestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def buildSystemPrompt(subject, level, style):
    return (
        f"You are {appTitle}, a patient and precise AI teaching assistant. "
        f"Subject focus: {subject}. Learner level: {level}. Teaching style: {style}. "
        "Format every answer in clean Markdown with clear headings, lists, and fenced code blocks where useful. "
        "Write all mathematics in LaTeX: inline expressions with $...$ and display equations with $$...$$. "
        "Check your reasoning before stating a result, and never invent citations. "
        "When a request is ambiguous, answer the most likely interpretation and end with one short clarifying question."
    )


def buildPayload(messages, subject, level, style):
    payload = [{"role": "system", "content": buildSystemPrompt(subject, level, style)}]
    for item in messages:
        payload.append({"role": item["role"], "content": item["content"]})
    return payload


def streamReply(client, payload, temperature):
    stream = client.chat.completions.create(
        model=model,
        messages=payload,
        temperature=temperature,
        max_completion_tokens=2048,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def buildMarkdownExport(messages, subject, level, style):
    lines = [
        f"# {appTitle} session",
        "",
        f"- **Subject:** {subject}",
        f"- **Level:** {level}",
        f"- **Style:** {style}",
        f"- **Model:** `{model}`",
        f"- **Exported:** {currentTimestamp()}",
        "",
        "---",
        "",
    ]
    for item in messages:
        speaker = "Learner" if item["role"] == "user" else "Tutor"
        lines.extend([f"## {speaker} · {item['time']}", "", item["content"], "", "---", ""])
    return "\n".join(lines)


def renderMessage(role, content):
    with st.chat_message(role):
        st.markdown(content)


def main():
    st.set_page_config(
        page_title=appTitle,
        page_icon="🎓",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    st.markdown(f"<style>{cssText}</style>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.markdown("## Desk")
        apiKeyInput = st.text_input(
            "Groq API key",
            value=os.environ.get("GROQ_API_KEY", ""),
            type="password",
            help="Used only for requests made in this session.",
        )
        subject = st.selectbox("Subject", subjectOptions)
        level = st.selectbox("Learner level", levelOptions, index=1)
        style = st.selectbox("Teaching style", styleOptions)
        temperature = st.slider("Creativity", 0.0, 1.0, 0.4, 0.05)
        st.caption(f"Model: {model}")

        exportText = buildMarkdownExport(st.session_state.messages, subject, level, style)
        st.download_button(
            "Export history (.md)",
            data=exportText,
            file_name=f"tutor-session-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}.md",
            mime="text/markdown",
            disabled=not st.session_state.messages,
        )
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.rerun()

    st.markdown('<h1 class="heroTitle">Tutor Atelier</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="heroLead">Ask, probe, and build understanding. Replies render Markdown and LaTeX, and your full session exports as a document.</p><div class="heroRule"></div>',
        unsafe_allow_html=True,
    )

    chosenStarter = None
    if not st.session_state.messages:
        starterCols = st.columns(len(starterPrompts))
        for index, (col, text) in enumerate(zip(starterCols, starterPrompts)):
            with col:
                if st.button(text, key=f"starter{index}"):
                    chosenStarter = text

    for item in st.session_state.messages:
        renderMessage(item["role"], item["content"])

    typed = st.chat_input("Ask a question, paste a problem, or request a worked example")
    prompt = typed or chosenStarter

    if prompt:
        if not apiKeyInput.strip():
            st.error("Add your Groq API key in the sidebar to start.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt, "time": currentTimestamp()})
        renderMessage("user", prompt)

        payload = buildPayload(st.session_state.messages, subject, level, style)
        reply = None
        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=apiKeyInput.strip())
                reply = st.write_stream(streamReply(client, payload, temperature))
            except Exception as error:
                st.error(f"Groq request failed: {error}")

        if reply:
            st.session_state.messages.append({"role": "assistant", "content": reply, "time": currentTimestamp()})
            st.rerun()
        else:
            st.session_state.messages.pop()


if __name__ == "__main__":
    main()