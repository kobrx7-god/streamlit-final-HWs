import datetime
import os

import streamlit as st
from groq import Groq

model = "openai/gpt-oss-120b"
appTitle = "Meridian Toolbox"
maxCompletionTokens = 3000
defaultTemperature = 0.4
sharedRules = (
    "Answer in clean Markdown with clear headings where they help. "
    "Write every mathematical expression in LaTeX, inline with $...$ and display with $$...$$. "
    "Be accurate, state uncertainty plainly, and never invent sources, quotations, statistics, or citations. "
    "End with a short next step or one question when it would help the user go further."
)

themeCss = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700;800&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --ink: #090a0f;
  --text: #eeece6;
  --dim: #9b9ca8;
  --glass: rgba(255, 255, 255, 0.035);
  --glassEdge: rgba(255, 255, 255, 0.09);
}

.stApp {
  background:
    radial-gradient(900px 700px at 8% -12%, color-mix(in srgb, var(--accent) 24%, transparent), transparent 60%),
    radial-gradient(800px 620px at 102% 18%, color-mix(in srgb, var(--accent) 11%, transparent), transparent 55%),
    radial-gradient(700px 520px at 42% 122%, rgba(120, 140, 255, 0.10), transparent 60%),
    var(--ink);
  color: var(--text);
  font-family: 'Instrument Sans', system-ui, sans-serif;
  transition: background 600ms ease;
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.07;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.55'/%3E%3C/svg%3E");
}

[data-testid="stHeader"] { background: transparent; }

.block-container {
  max-width: 1040px;
  padding-top: 2.4rem;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), transparent 35%), #07080c;
  border-right: 1px solid var(--glassEdge);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] p {
  color: var(--dim);
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--accent) 30%, transparent);
  border-radius: 8px;
}

.brandMark {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif;
  font-weight: 800;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
  color: var(--text);
  padding: 0.2rem 0 0.4rem;
}

.brandMark::after {
  content: "";
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-left: 0.5rem;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 16px var(--accent);
  vertical-align: middle;
}

[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  justify-content: flex-start;
  text-align: left;
  border-radius: 12px;
  padding: 0.65rem 0.9rem;
  font-weight: 500;
  color: var(--dim);
  background: transparent;
  border: 1px solid transparent;
  transition: all 240ms cubic-bezier(.2, .7, .2, 1);
}

[data-testid="stSidebar"] .stButton > button:hover {
  color: var(--text);
  background: var(--glass);
  border-color: var(--glassEdge);
  transform: translateX(3px);
}

[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  color: var(--text);
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 24%, transparent), transparent 92%);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
  box-shadow: inset 3px 0 0 var(--accent), 0 0 30px color-mix(in srgb, var(--accent) 12%, transparent);
}

.heroWrap {
  display: flex;
  align-items: flex-end;
  gap: 1.3rem;
  margin: 0.4rem 0 1.9rem;
  animation: riseIn 820ms cubic-bezier(.2, .7, .2, 1) both;
}

.heroGlyph {
  font-size: 4.8rem;
  line-height: 0.9;
  color: var(--accent);
  text-shadow: 0 0 44px color-mix(in srgb, var(--accent) 55%, transparent);
}

.heroTitle {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif;
  font-weight: 800;
  font-size: clamp(2.4rem, 6vw, 4.4rem);
  letter-spacing: -0.04em;
  line-height: 0.95;
  margin: 0;
  color: var(--text);
}

.heroLead {
  color: var(--dim);
  font-size: 1.05rem;
  line-height: 1.5;
  max-width: 46ch;
  margin: 0.7rem 0 0;
}

@keyframes riseIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] input {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid var(--glassEdge) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent) !important;
}

[data-testid="stSlider"] div[role="slider"] {
  background: var(--accent) !important;
  box-shadow: 0 0 14px var(--accent);
}

.block-container .stButton > button {
  background: var(--glass);
  color: var(--text);
  border: 1px solid var(--glassEdge);
  border-radius: 999px;
  padding: 0.55rem 1rem;
  font-size: 0.92rem;
  backdrop-filter: blur(10px);
  transition: all 220ms ease;
}

.block-container .stButton > button p {
  white-space: normal;
  text-align: left;
  line-height: 1.35;
}

.block-container .stButton > button:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  box-shadow: 0 0 24px color-mix(in srgb, var(--accent) 18%, transparent);
}

.block-container .stButton > button:focus-visible,
[data-testid="stSidebar"] .stButton > button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

[data-testid="stChatMessage"] {
  background: var(--glass);
  border: 1px solid var(--glassEdge);
  border-radius: 20px 20px 20px 4px;
  padding: 1rem 1.3rem;
  margin: 0.9rem 0;
  backdrop-filter: blur(14px);
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  background: color-mix(in srgb, var(--accent) 9%, transparent);
  border-color: color-mix(in srgb, var(--accent) 28%, transparent);
  margin-left: 14%;
  border-radius: 20px 20px 4px 20px;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
  line-height: 1.7;
  font-size: 1.01rem;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3 {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text);
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] table {
  display: block;
  overflow-x: auto;
  border-collapse: collapse;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] th,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] td {
  border: 1px solid var(--glassEdge);
  padding: 0.4rem 0.7rem;
}

.katex-display { overflow-x: auto; overflow-y: hidden; padding: 0.3rem 0; }

code, pre {
  font-family: 'JetBrains Mono', ui-monospace, monospace !important;
}

pre {
  background: rgba(0, 0, 0, 0.45) !important;
  border: 1px solid var(--glassEdge);
  border-radius: 14px;
}

[data-testid="stChatInput"] {
  background: rgba(10, 11, 16, 0.82);
  border: 1px solid var(--glassEdge);
  border-radius: 18px;
  backdrop-filter: blur(16px);
  transition: box-shadow 240ms ease, border-color 240ms ease;
}

[data-testid="stChatInput"]:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 16%, transparent), 0 0 40px color-mix(in srgb, var(--accent) 12%, transparent);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
  }
}
"""

domainRegistry = [
    {
        "key": "general",
        "label": "General",
        "glyph": "◎",
        "accent": "#f5f1e6",
        "tagline": "Everyday reasoning, writing, and planning, shaped into clear structure.",
        "contextLabel": "Audience or goal",
        "contextPlaceholder": "e.g. a busy manager, a first-time traveler",
        "placeholder": "Ask anything, or paste text to work on",
        "tasks": {
            "Converse": "Answer the question directly and helpfully, matching depth to the request.",
            "Summarize text": "Summarize the pasted text in a few tight bullets, then give a one-sentence takeaway.",
            "Rewrite": "Rewrite the user's text for clarity and tone while keeping its meaning. Offer one alternative version.",
            "Brainstorm": "Generate eight distinct ideas grouped by theme, each with a one-line rationale.",
            "Plan": "Turn the goal into a sequenced plan with milestones, risks, and a concrete first action for today.",
        },
        "starters": [
            "Plan a week of focused study sessions",
            "Summarize the tradeoffs of remote work",
            "Brainstorm names for a community garden",
        ],
    },
    {
        "key": "math",
        "label": "Mathematics",
        "glyph": "∑",
        "accent": "#8fb4ff",
        "tagline": "Solve, prove, and visualize, with every step rendered in LaTeX.",
        "contextLabel": "Level or topic",
        "contextPlaceholder": "e.g. linear algebra, first-year calculus",
        "placeholder": "State a problem, a proof, or a concept to explore",
        "tasks": {
            "Solve": "Solve the problem. Show each step in LaTeX, justify the key moves, and box the final answer.",
            "Explain concept": "Explain the concept from intuition to formal definition, with one worked example and one common misconception.",
            "Check proof": "Check the user's proof line by line. Mark each step valid or flawed, and say exactly where it breaks.",
            "Practice set": "Create five graded practice problems, then a separate section headed Solutions with full answers.",
            "Estimate": "Give an order-of-magnitude estimate with explicit assumptions, then identify the most sensitive assumption and refine around it.",
        },
        "starters": [
            "Solve the integral of x e^x",
            "Explain why the determinant measures scaling",
            "Prove there are infinitely many primes",
        ],
    },
    {
        "key": "science",
        "label": "Science",
        "glyph": "⚛",
        "accent": "#5ee2c4",
        "tagline": "Mechanisms, experiments, and data, explained with the evidence behind them.",
        "contextLabel": "Discipline",
        "contextPlaceholder": "e.g. organic chemistry, ecology, astrophysics",
        "placeholder": "Ask how something works, or paste data to analyze",
        "tasks": {
            "Explain mechanism": "Explain the mechanism step by step, distinguishing established findings from active research.",
            "Design experiment": "Design a controlled experiment: hypothesis, variables, controls, sample size reasoning, and likely confounders.",
            "Analyze data": "The user will paste data or results. Describe the pattern, suggest suitable statistics, and flag anything that looks like an artifact.",
            "Critique study": "Assess the study's design, sample, measurement, and conclusions. Separate what is supported from what is overreached.",
            "Units and estimates": "Do dimensional analysis and back-of-envelope estimates. Show units at every step.",
        },
        "starters": [
            "How do vaccines train the immune system?",
            "Design an experiment to test plant growth under blue light",
            "Explain why the sky is blue, with the math",
        ],
    },
    {
        "key": "languages",
        "label": "Languages",
        "glyph": "文",
        "accent": "#ff8fa3",
        "tagline": "Translate, correct, converse, and untangle grammar, one sentence at a time.",
        "contextLabel": "Target language",
        "contextPlaceholder": "e.g. Japanese, Portuguese (Brazil)",
        "placeholder": "Paste text to translate or correct, or start a conversation",
        "tasks": {
            "Translate": "Translate the user's text into the target language. Give the translation first, then notes on idioms, register, and ambiguity.",
            "Correct": "Correct the user's text in the target language. List each change with a short grammar reason, then give the corrected text.",
            "Converse": "Hold a short conversation in the target language, one turn at a time. Follow with a brief English note on any error the learner made.",
            "Explain grammar": "Explain the grammar point with a table of forms and three example sentences, each with a gloss.",
            "Drill": "Create a six-item drill for the named grammar point or vocabulary, with answers in a separate section headed Answers.",
        },
        "starters": [
            "Translate: The meeting was moved to Thursday",
            "Explain the subjunctive in Spanish",
            "Start a beginner conversation in French",
        ],
    },
    {
        "key": "history",
        "label": "History",
        "glyph": "⧖",
        "accent": "#d9a45b",
        "tagline": "Timelines, sources, and counterfactuals, weighed with historiographical care.",
        "contextLabel": "Region or era",
        "contextPlaceholder": "e.g. Ottoman Balkans, 1870 to 1914",
        "placeholder": "Ask about an event, paste a source, or request a timeline",
        "tasks": {
            "Timeline": "Build a dated timeline of key events, each with a one-line significance note. Mark uncertain dates explicitly.",
            "Analyze source": "Analyze the user's source text: author, context, audience, purpose, reliability, and what it omits.",
            "Compare causes": "Compare competing historiographical explanations. For each, note the evidence it relies on and where historians disagree.",
            "Counterfactual": "Explore a plausible counterfactual with labeled assumptions, the most likely ripple effects, and the limits of the exercise.",
            "Explain event": "Explain the event in this order: background, immediate triggers, key actors, outcomes, and lasting legacy.",
        },
        "starters": [
            "Timeline of the Silk Road's main routes",
            "What caused the fall of the Western Roman Empire?",
            "Counterfactual: no Treaty of Versailles",
        ],
    },
    {
        "key": "geopolitics",
        "label": "Geopolitics",
        "glyph": "◈",
        "accent": "#b89cff",
        "tagline": "Briefings, stakeholder maps, and scenarios across power, policy, and trade.",
        "contextLabel": "Region of interest",
        "contextPlaceholder": "e.g. Red Sea shipping, Arctic routes",
        "placeholder": "Name a region, actor, agreement, or question to brief",
        "tasks": {
            "Briefing": "Write a neutral briefing: background, current state, key actors and their interests, and what to watch next. Attribute contested claims to the position holding them.",
            "Stakeholder map": "Map the stakeholders as a table with columns for actor, stated interests, leverage, likely position, and constraints.",
            "Scenario analysis": "Build three scenarios (base, escalation, de-escalation) with drivers and indicators. Use qualitative likelihood language rather than precise percentages.",
            "Explain agreement": "Explain the treaty or agreement: parties, obligations, enforcement, known gaps, and where it is contested.",
            "Steelman": "Present the strongest version of the position the user names, then its strongest objections, without taking a side on contested values.",
        },
        "starters": [
            "Briefing: Arctic shipping routes",
            "Scenario analysis for Taiwan Strait tensions",
            "Explain the Montreal Protocol",
        ],
    },
    {
        "key": "environmental",
        "label": "Environmental",
        "glyph": "◍",
        "accent": "#9ad65c",
        "tagline": "Climate, ecosystems, and impact, quantified with ranges and actionable next steps.",
        "contextLabel": "Location or ecosystem",
        "contextPlaceholder": "e.g. Lake Victoria, a coastal mangrove",
        "placeholder": "Describe a project, habit, species, or climate question",
        "tasks": {
            "Impact assessment": "Assess the environmental impact: pathways, magnitude ranges, uncertainty, and mitigation options ranked by effectiveness.",
            "Carbon estimate": "Estimate emissions with explicit activity data and emission factors, state the type of source for each factor, give a range, and name the most uncertain factor.",
            "Climate explainer": "Explain the mechanism or indicator clearly, with the evidence base, and what the trend data does and does not show.",
            "Action plan": "Create a prioritized action plan for an individual, household, or organization, sorted by impact per unit of effort, with costs flagged.",
            "Species and habitat": "Describe the ecology: range, threats, role in the ecosystem, conservation status, and gaps in the data.",
        },
        "starters": [
            "Estimate the footprint of a 10 km daily commute by car",
            "Explain ocean acidification simply",
            "Action plan to cut household waste",
        ],
    },
]


def currentTimestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def findDomain(key):
    for spec in domainRegistry:
        if spec["key"] == key:
            return spec
    return domainRegistry[0]


def resolveApiKey(inputValue):
    cleaned = inputValue.strip()
    if cleaned:
        return cleaned
    return os.environ.get("GROQ_API_KEY", "").strip()


def buildSystemPrompt(spec, taskName, contextDetail):
    taskInstruction = spec["tasks"][taskName]
    contextLine = contextDetail.strip() or "not specified; infer a sensible default and say so briefly"
    return (
        f"You are the {spec['label']} assistant inside {appTitle}. "
        f"Current mode: {taskName}. Mode instruction: {taskInstruction} "
        f"{spec['contextLabel']}: {contextLine}. "
        f"{sharedRules}"
    )


def buildPayload(messages, systemPrompt):
    payload = [{"role": "system", "content": systemPrompt}]
    for item in messages:
        payload.append({"role": item["role"], "content": item["content"]})
    return payload


def streamReply(apiKey, payload, temperature):
    client = Groq(api_key=apiKey)
    stream = client.chat.completions.create(
        model=model,
        messages=payload,
        temperature=temperature,
        max_completion_tokens=maxCompletionTokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def buildMarkdownExport(domainLabel, taskName, contextDetail, messages):
    lines = [
        f"# {appTitle} · {domainLabel}",
        "",
        f"- **Mode:** {taskName}",
        f"- **Context:** {contextDetail.strip() or 'unspecified'}",
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


def exportFileName(domainKey):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    return f"meridian-{domainKey}-{stamp}.md"


def buildThemeMarkup(accent):
    return f"<style>:root {{ --accent: {accent}; }}\n{themeCss}</style>"


def setActiveDomain(key):
    st.session_state.activeDomain = key


def clearDomainHistory(key):
    st.session_state[f"messages_{key}"] = []


def renderHero(spec):
    st.markdown(
        f'<div class="heroWrap"><span class="heroGlyph">{spec["glyph"]}</span>'
        f'<div><h1 class="heroTitle">{spec["label"]}</h1>'
        f'<p class="heroLead">{spec["tagline"]}</p></div></div>',
        unsafe_allow_html=True,
    )


def renderMessage(role, content):
    with st.chat_message(role):
        st.markdown(content)


def renderWorkspace(spec, apiKey, temperature):
    key = spec["key"]
    messagesKey = f"messages_{key}"
    taskKey = f"task_{key}"
    contextKey = f"context_{key}"

    if messagesKey not in st.session_state:
        st.session_state[messagesKey] = []

    renderHero(spec)

    taskNames = list(spec["tasks"].keys())
    leftCol, rightCol = st.columns([1, 1.6])
    with leftCol:
        taskName = st.selectbox("Mode", taskNames, key=taskKey)
    with rightCol:
        contextDetail = st.text_input(
            spec["contextLabel"],
            key=contextKey,
            placeholder=spec["contextPlaceholder"],
        )

    messages = st.session_state[messagesKey]

    chosenStarter = None
    if not messages:
        starterCols = st.columns(len(spec["starters"]))
        for index, (col, text) in enumerate(zip(starterCols, spec["starters"])):
            with col:
                if st.button(text, key=f"starter_{key}_{index}"):
                    chosenStarter = text

    for item in messages:
        renderMessage(item["role"], item["content"])

    typed = st.chat_input(spec["placeholder"], key=f"input_{key}")
    prompt = typed or chosenStarter

    if not prompt:
        return

    if not apiKey:
        st.error("Add a Groq API key in the sidebar to start.")
        return

    messages.append({"role": "user", "content": prompt, "time": currentTimestamp()})
    renderMessage("user", prompt)

    systemPrompt = buildSystemPrompt(spec, taskName, contextDetail)
    payload = buildPayload(messages, systemPrompt)

    reply = None
    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(streamReply(apiKey, payload, temperature))
        except Exception as error:
            st.error(f"Groq request failed: {error}")

    if reply:
        messages.append({"role": "assistant", "content": reply, "time": currentTimestamp()})
        st.rerun()
    else:
        messages.pop()


def main():
    st.set_page_config(
        page_title=appTitle,
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "activeDomain" not in st.session_state:
        st.session_state.activeDomain = domainRegistry[0]["key"]

    activeSpec = findDomain(st.session_state.activeDomain)
    activeKey = activeSpec["key"]

    st.markdown(buildThemeMarkup(activeSpec["accent"]), unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f'<div class="brandMark">{appTitle}</div>', unsafe_allow_html=True)

        for spec in domainRegistry:
            st.button(
                f"{spec['glyph']}   {spec['label']}",
                key=f"nav_{spec['key']}",
                on_click=setActiveDomain,
                args=(spec["key"],),
                type="primary" if spec["key"] == activeKey else "secondary",
            )

        st.divider()
        apiKeyInput = st.text_input(
            "Groq API key",
            value=os.environ.get("GROQ_API_KEY", ""),
            type="password",
            help="Used only for requests made in this session.",
        )
        temperature = st.slider("Creativity", 0.0, 1.0, defaultTemperature, 0.05)
        st.caption(f"Model · {model}")

    renderWorkspace(activeSpec, resolveApiKey(apiKeyInput), temperature)

    with st.sidebar:
        st.divider()
        messages = st.session_state.get(f"messages_{activeKey}", [])
        taskName = st.session_state.get(f"task_{activeKey}", list(activeSpec["tasks"].keys())[0])
        contextDetail = st.session_state.get(f"context_{activeKey}", "")
        exportText = buildMarkdownExport(activeSpec["label"], taskName, contextDetail, messages)
        st.download_button(
            "Export this room (.md)",
            data=exportText,
            file_name=exportFileName(activeKey),
            mime="text/markdown",
            disabled=not messages,
        )
        st.button(
            "Clear this room",
            key=f"clear_{activeKey}",
            on_click=clearDomainHistory,
            args=(activeKey,),
        )


if __name__ == "__main__":
    main()
