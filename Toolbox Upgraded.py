import datetime
import os
import re

import streamlit as st
from groq import Groq

model = "openai/gpt-oss-120b"
appTitle = "Meridian Toolbox"
maxCompletionTokens = 2200
defaultTemperature = 0.4
defaultTurnBudget = 6
transcriptWindow = 24
sharedRules = (
    "Write every mathematical expression in LaTeX, inline with $...$ and display with $$...$$. "
    "Be accurate, state uncertainty plainly, and never invent sources, quotations, statistics, or citations. "
    "Use clean Markdown where it helps."
)

agentRegistry = {
    "atlas": {
        "name": "Atlas",
        "role": "Generalist synthesizer",
        "emoji": "🧭",
        "tone": "#f5f1e6",
        "persona": "Pragmatic and plain-spoken. Turns tangled discussions into clear next steps.",
    },
    "euler": {
        "name": "Euler",
        "role": "Mathematician",
        "emoji": "🧮",
        "tone": "#8fb4ff",
        "persona": "Rigorous and precise. Demands definitions, checks each algebraic step, and prefers a short proof to a long argument.",
    },
    "curie": {
        "name": "Curie",
        "role": "Experimental scientist",
        "emoji": "🔬",
        "tone": "#5ee2c4",
        "persona": "Evidence-first. Asks what would falsify a claim and how it could be measured.",
    },
    "babel": {
        "name": "Babel",
        "role": "Linguist",
        "emoji": "🗣️",
        "tone": "#ff8fa3",
        "persona": "Attentive to register, idiom, and meaning across languages. Notices what translation loses.",
    },
    "clio": {
        "name": "Clio",
        "role": "Historian",
        "emoji": "🏛️",
        "tone": "#d9a45b",
        "persona": "Contextual and source-minded. Warns against anachronism and weighs competing historiographies.",
    },
    "metternich": {
        "name": "Metternich",
        "role": "Geopolitical strategist",
        "emoji": "🌐",
        "tone": "#b89cff",
        "persona": "Thinks in interests, leverage, and constraints. Maps actors and second-order effects without moralizing.",
    },
    "gaia": {
        "name": "Gaia",
        "role": "Environmental scientist",
        "emoji": "🌿",
        "tone": "#9ad65c",
        "persona": "Systems-minded. Thinks in ranges, feedback loops, and tradeoffs between ecological and human costs.",
    },
    "sable": {
        "name": "Sable",
        "role": "Red-team skeptic",
        "emoji": "🧐",
        "tone": "#ff6b6b",
        "persona": "Challenges weak claims and hidden assumptions. Asks for evidence. Concedes cleanly when persuaded.",
    },
    "nexus": {
        "name": "Nexus",
        "role": "Moderator",
        "emoji": "🧠",
        "tone": "#ffffff",
        "persona": "Neutral chair. Summarizes agreements, disagreements, open questions, and a recommendation, crediting colleagues by @Name.",
    },
}

roomRegistry = [
    {
        "key": "general",
        "label": "General",
        "glyph": "◎",
        "accent": "#f5f1e6",
        "tagline": "Everyday reasoning, writing, and planning, shaped into clear structure.",
        "contextLabel": "Audience or goal",
        "contextPlaceholder": "e.g. a busy manager, a first-time traveler",
        "placeholder": "Ask anything, or paste text to work on",
        "roster": ["atlas", "sable"],
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
        "roster": ["euler", "sable", "atlas"],
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
        "roster": ["curie", "sable", "euler"],
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
        "roster": ["babel", "atlas", "sable"],
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
        "roster": ["clio", "sable", "metternich"],
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
        "roster": ["metternich", "clio", "sable"],
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
        "roster": ["gaia", "curie", "atlas", "sable"],
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
    {
        "key": "council",
        "label": "Council",
        "glyph": "✦",
        "accent": "#ff9f6e",
        "tagline": "Agents from every field at one table, challenging and referring to each other by name.",
        "contextLabel": "Shared question or brief",
        "contextPlaceholder": "e.g. should a city ban cars from its downtown core?",
        "placeholder": "Put a question on the table",
        "roster": ["atlas", "euler", "curie", "clio", "metternich", "gaia", "sable"],
        "council": True,
        "tasks": {
            "Debate": "Argue the question from each agent's field. Disagree openly where fields conflict and name who you are responding to.",
            "Joint research brief": "Produce a shared research brief: consensus, contested points, evidence gaps, and who should investigate what.",
            "Red-team a plan": "Stress-test the user's plan. Each agent attacks it from their discipline, then proposes a fix.",
            "Interdisciplinary explainer": "Explain the topic so each field contributes one layer, building from intuition to technical depth.",
            "Decision memo": "Draft a decision memo with options, tradeoffs, a recommended option, and what would change the recommendation.",
        },
        "starters": [
            "Should a city ban cars from its downtown core?",
            "Red-team a plan to replace coal with solar and storage",
            "Is a universal basic income affordable and wise?",
        ],
    },
]

themeCss = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700;800&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

@property --spin {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

:root {
  --ink: #07080d;
  --text: #eeece6;
  --dim: #9b9ca8;
  --glass: rgba(255, 255, 255, 0.035);
  --glassEdge: rgba(255, 255, 255, 0.09);
}

.stApp {
  background:
    radial-gradient(900px 700px at 8% -12%, color-mix(in srgb, var(--accent) 24%, transparent), transparent 60%),
    radial-gradient(800px 620px at 102% 18%, color-mix(in srgb, var(--accent) 11%, transparent), transparent 55%),
    radial-gradient(700px 520px at 42% 122%, rgba(120, 140, 255, 0.12), transparent 60%),
    var(--ink);
  color: var(--text);
  font-family: 'Instrument Sans', system-ui, sans-serif;
  transition: background 600ms ease;
  overflow-x: hidden;
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.08;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.55'/%3E%3C/svg%3E");
}

.stApp::after {
  content: "";
  position: fixed;
  width: 62vmax;
  height: 62vmax;
  left: -22vmax;
  top: -26vmax;
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(closest-side, color-mix(in srgb, var(--accent) 16%, transparent), transparent);
  filter: blur(30px);
  animation: orbFloat 24s ease-in-out infinite alternate;
}

@keyframes orbFloat {
  to { transform: translate(22vw, 14vh) scale(1.18); }
}

[data-testid="stHeader"] { background: transparent; }

.block-container {
  max-width: 1080px;
  padding-top: 2.2rem;
  position: relative;
  z-index: 1;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent 35%), #06070b;
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
  font-size: 1.2rem;
  letter-spacing: -0.02em;
  padding: 0.2rem 0 0.6rem;
  background: linear-gradient(100deg, var(--text) 40%, var(--accent));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.brandMark::after {
  content: "";
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-left: 0.5rem;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 16px var(--accent), 0 0 40px var(--accent);
  vertical-align: middle;
  animation: pulseDot 2.4s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.55; }
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
  transform: translateX(4px);
}

[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  color: var(--text);
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 26%, transparent), transparent 92%);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
  box-shadow: inset 3px 0 0 var(--accent), 0 0 34px color-mix(in srgb, var(--accent) 14%, transparent);
}

.ticker {
  overflow: hidden;
  border-top: 1px solid var(--glassEdge);
  border-bottom: 1px solid var(--glassEdge);
  padding: 0.55rem 0;
  margin: 0 0 1.8rem;
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
}

.tickerTrack {
  display: flex;
  gap: 2.4rem;
  width: max-content;
  white-space: nowrap;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.78rem;
  color: var(--dim);
  animation: tickerRun 42s linear infinite;
}

.tickerTrack b {
  font-weight: 500;
  color: var(--text);
}

@keyframes tickerRun {
  to { transform: translateX(-50%); }
}

.heroWrap {
  display: flex;
  align-items: center;
  gap: 1.6rem;
  margin: 0.2rem 0 1.4rem;
  animation: riseIn 820ms cubic-bezier(.2, .7, .2, 1) both;
}

.heroGlyph {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 5.6rem;
  height: 5.6rem;
  flex-shrink: 0;
  border-radius: 50%;
  font-size: 2.5rem;
  line-height: 1;
  color: var(--accent);
  background: radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.12), transparent 60%), var(--glass);
  border: 1px solid var(--glassEdge);
  text-shadow: 0 0 30px var(--accent);
}

.heroGlyph::before {
  content: "";
  position: absolute;
  inset: -7px;
  border-radius: 50%;
  background: conic-gradient(from var(--spin), var(--accent), transparent 25%, var(--accent) 50%, transparent 75%, var(--accent));
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #000 calc(100% - 1px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #000 calc(100% - 1px));
  animation: spinHalo 6s linear infinite;
}

@keyframes spinHalo {
  to { --spin: 360deg; }
}

.heroTitle {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif;
  font-weight: 800;
  font-size: clamp(2.4rem, 6vw, 4.4rem);
  letter-spacing: -0.045em;
  line-height: 0.95;
  margin: 0;
  background: linear-gradient(100deg, var(--text) 45%, color-mix(in srgb, var(--accent) 70%, #ffffff));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.heroLead {
  color: var(--dim);
  font-size: 1.05rem;
  line-height: 1.5;
  max-width: 50ch;
  margin: 0.7rem 0 0;
}

@keyframes riseIn {
  from { opacity: 0; transform: translateY(14px); filter: blur(6px); }
  to { opacity: 1; transform: none; filter: none; }
}

.rosterRow {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0 0 1.5rem;
}

.rosterPill,
.agentTag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--tone);
  border: 1px solid color-mix(in srgb, var(--tone) 42%, transparent);
  background: color-mix(in srgb, var(--tone) 11%, transparent);
  border-radius: 999px;
  box-shadow: 0 0 18px color-mix(in srgb, var(--tone) 16%, transparent);
  white-space: nowrap;
}

.rosterPill {
  padding: 0.3rem 0.8rem;
  font-size: 0.84rem;
  font-weight: 500;
}

.agentTag {
  padding: 0.26rem 0.7rem;
  margin-bottom: 0.55rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.74rem;
}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid var(--glassEdge) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}

[data-testid="stMultiSelect"] [data-baseweb="tag"] {
  background: color-mix(in srgb, var(--accent) 18%, transparent) !important;
  border-radius: 999px !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent) !important;
}

[data-testid="stRadio"] div[role="radiogroup"] {
  gap: 0.4rem;
}

[data-testid="stRadio"] div[role="radiogroup"] > label {
  border: 1px solid var(--glassEdge);
  border-radius: 999px;
  padding: 0.22rem 0.85rem;
  background: var(--glass);
  transition: all 200ms ease;
}

[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 14%, transparent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--accent) 22%, transparent);
}

[data-testid="stSlider"] div[role="slider"] {
  background: var(--accent) !important;
  box-shadow: 0 0 14px var(--accent);
}

.block-container .stButton > button {
  position: relative;
  overflow: hidden;
  background: var(--glass);
  color: var(--text);
  border: 1px solid var(--glassEdge);
  border-radius: 999px;
  padding: 0.55rem 1rem;
  font-size: 0.92rem;
  backdrop-filter: blur(10px);
  transition: all 220ms ease;
}

.block-container .stButton > button::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255, 255, 255, 0.2) 50%, transparent 70%);
  transform: translateX(-120%);
  pointer-events: none;
}

.block-container .stButton > button:hover::after {
  animation: sweep 720ms ease forwards;
}

@keyframes sweep {
  to { transform: translateX(120%); }
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
  box-shadow: 0 0 28px color-mix(in srgb, var(--accent) 20%, transparent);
  transform: translateY(-2px);
}

.block-container .stButton > button:focus-visible,
[data-testid="stSidebar"] .stButton > button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

[data-testid="stChatMessage"] {
  background: var(--glass);
  border: 1px solid var(--glassEdge);
  border-radius: 22px 22px 22px 6px;
  padding: 1.05rem 1.35rem;
  margin: 1rem 0;
  backdrop-filter: blur(14px);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.25);
  animation: riseIn 520ms cubic-bezier(.2, .7, .2, 1) both;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  background: color-mix(in srgb, var(--accent) 9%, transparent);
  border-color: color-mix(in srgb, var(--accent) 28%, transparent);
  margin-left: 14%;
  border-radius: 22px 22px 6px 22px;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
  line-height: 1.72;
  font-size: 1.01rem;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong {
  color: var(--accent);
  font-weight: 600;
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
  background: rgba(8, 9, 14, 0.85);
  border: 1px solid var(--glassEdge);
  border-radius: 20px;
  backdrop-filter: blur(16px);
  transition: box-shadow 240ms ease, border-color 240ms ease;
}

[data-testid="stChatInput"]:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 16%, transparent), 0 0 46px color-mix(in srgb, var(--accent) 14%, transparent);
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


def findRoom(key):
    for room in roomRegistry:
        if room["key"] == key:
            return room
    return roomRegistry[0]


def keyForName(name):
    for key, agent in agentRegistry.items():
        if agent["name"].lower() == name.lower():
            return key
    return None


def agentLabel(key):
    agent = agentRegistry[key]
    return f"{agent['emoji']} {agent['name']} · {agent['role']}"


def currentRoster(room):
    if room.get("council"):
        return st.session_state.get(f"roster_{room['key']}", room["roster"])
    return room["roster"]


def resolveApiKey(inputValue):
    cleaned = inputValue.strip()
    if cleaned:
        return cleaned
    return os.environ.get("GROQ_API_KEY", "").strip()


def speakerName(item):
    if item["role"] == "user":
        return "User"
    return agentRegistry[item["agent"]]["name"]


def buildTranscript(history):
    window = history[-transcriptWindow:]
    return "\n\n".join(f"[{speakerName(item)}] {item['content']}" for item in window)


def buildTurnPayload(systemPrompt, history):
    transcript = buildTranscript(history)
    return [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": f"Conversation so far:\n\n{transcript}\n\nTake your turn now."},
    ]


def buildAgentSystemPrompt(agentKey, room, taskName, contextDetail, roster, isSolo):
    agent = agentRegistry[agentKey]
    colleagues = [agentRegistry[key] for key in roster if key != agentKey]
    colleagueLine = "; ".join(f"{c['name']} ({c['role']})" for c in colleagues) or "none; you work alone"
    contextLine = contextDetail.strip() or "not specified; infer a sensible default and say so briefly"
    teamLine = (
        "You are working alone in this room."
        if isSolo
        else "This is a live roundtable. Build on, challenge, or correct colleagues by name."
    )
    return (
        f"You are {agent['name']}, the {agent['role']} in {appTitle}. "
        f"Persona: {agent['persona']} "
        f"Room: {room['label']}. Mode: {taskName}. Mode instruction: {room['tasks'][taskName]} "
        f"{room['contextLabel']}: {contextLine}. "
        f"Colleagues: {colleagueLine}. {teamLine} "
        "Speak only as yourself and never write lines for other agents or the user. "
        "When you refer to a colleague, write their name with an @ prefix, such as @Euler. "
        "If you need one specific colleague to weigh in before you can finish, end your message with [[ask: Name]] naming exactly one colleague. "
        "Keep your turn focused and under 220 words unless the task truly needs more. "
        f"{sharedRules}"
    )


def buildModeratorSystemPrompt(room, taskName, contextDetail):
    moderator = agentRegistry["nexus"]
    contextLine = contextDetail.strip() or "not specified"
    return (
        f"You are {moderator['name']}, the {moderator['role']} in {appTitle}. "
        f"Persona: {moderator['persona']} "
        f"Room: {room['label']}. Mode: {taskName}. "
        f"{room['contextLabel']}: {contextLine}. "
        "Close this roundtable with a synthesis: where agents agree, where they disagree, the open questions, "
        "and one recommended next step. Credit colleagues by @Name. Keep it under 260 words. "
        f"{sharedRules}"
    )


def parseAsks(text):
    pattern = r"\[\[\s*ask\s*:\s*([A-Za-z]+)\s*\]\]"
    targets = []
    for name in re.findall(pattern, text, flags=re.IGNORECASE):
        key = keyForName(name)
        if key and key not in targets:
            targets.append(key)
    cleaned = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    return cleaned, targets


def highlightMentions(text):
    result = text
    for agent in agentRegistry.values():
        result = re.sub(rf"@{re.escape(agent['name'])}\b", f"**@{agent['name']}**", result)
    return result


def agentTagHtml(agent):
    return f'<span class="agentTag" style="--tone:{agent["tone"]}">{agent["emoji"]} {agent["name"]} · {agent["role"]}</span>'


def renderEntry(item):
    if item["role"] == "user":
        with st.chat_message("user"):
            st.markdown(item["content"])
        return
    agent = agentRegistry[item["agent"]]
    with st.chat_message(agent["name"], avatar=agent["emoji"]):
        st.markdown(agentTagHtml(agent), unsafe_allow_html=True)
        st.markdown(highlightMentions(item["content"]))


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


def streamAgentTurn(agent, systemPrompt, history, apiKey, temperature):
    payload = buildTurnPayload(systemPrompt, history)
    raw = None
    with st.chat_message(agent["name"], avatar=agent["emoji"]):
        st.markdown(agentTagHtml(agent), unsafe_allow_html=True)
        try:
            raw = st.write_stream(streamReply(apiKey, payload, temperature))
        except Exception as error:
            st.error(f"Groq request failed: {error}")
    return raw


def runDeliberation(room, roster, isSolo, taskName, contextDetail, messages, apiKey, temperature, turnBudget):
    queue = list(roster)
    budget = 1 if isSolo else turnBudget
    newEntries = []
    spoken = 0
    failed = False

    while queue and spoken < budget and not failed:
        agentKey = queue.pop(0)
        agent = agentRegistry[agentKey]
        systemPrompt = buildAgentSystemPrompt(agentKey, room, taskName, contextDetail, roster, isSolo)
        raw = streamAgentTurn(agent, systemPrompt, messages + newEntries, apiKey, temperature)
        if raw is None:
            failed = True
            break
        cleaned, targets = parseAsks(raw)
        newEntries.append({"role": "assistant", "agent": agentKey, "content": cleaned, "time": currentTimestamp()})
        spoken += 1
        if not isSolo:
            for target in reversed(targets):
                if target in roster and target != agentKey:
                    if target in queue:
                        queue.remove(target)
                    queue.insert(0, target)

    if not isSolo and newEntries and not failed:
        moderatorPrompt = buildModeratorSystemPrompt(room, taskName, contextDetail)
        raw = streamAgentTurn(agentRegistry["nexus"], moderatorPrompt, messages + newEntries, apiKey, temperature)
        if raw is None:
            failed = True
        else:
            newEntries.append({"role": "assistant", "agent": "nexus", "content": raw.strip(), "time": currentTimestamp()})

    messages.extend(newEntries)
    if newEntries and not failed:
        st.rerun()
    return len(newEntries)


def renderHero(room):
    st.markdown(
        f'<div class="heroWrap"><span class="heroGlyph">{room["glyph"]}</span>'
        f'<div><h1 class="heroTitle">{room["label"]}</h1>'
        f'<p class="heroLead">{room["tagline"]}</p></div></div>',
        unsafe_allow_html=True,
    )


def renderRosterPills(roster):
    pills = "".join(
        f'<span class="rosterPill" style="--tone:{agentRegistry[key]["tone"]}">'
        f'{agentRegistry[key]["emoji"]} {agentRegistry[key]["name"]}</span>'
        for key in roster
    )
    st.markdown(f'<div class="rosterRow">{pills}</div>', unsafe_allow_html=True)


def renderTicker():
    names = "".join(
        f'<span><b>{agent["emoji"]} {agent["name"]}</b> · {agent["role"]}</span>'
        for agent in agentRegistry.values()
    )
    st.markdown(
        f'<div class="ticker"><div class="tickerTrack">{names}{names}</div></div>',
        unsafe_allow_html=True,
    )


def renderRoom(room, apiKey, temperature, turnBudget):
    key = room["key"]
    messagesKey = f"messages_{key}"
    taskKey = f"task_{key}"
    contextKey = f"context_{key}"
    modeKey = f"mode_{key}"
    rosterKey = f"roster_{key}"

    if messagesKey not in st.session_state:
        st.session_state[messagesKey] = []

    renderHero(room)

    if room.get("council"):
        options = [agentKey for agentKey in agentRegistry if agentKey != "nexus"]
        st.multiselect(
            "Agents at the table",
            options,
            default=room["roster"],
            key=rosterKey,
            format_func=agentLabel,
        )
        roster = currentRoster(room)
        if not roster:
            st.warning("Seat at least one agent at the table.")
            return
        modeOptions = ["Roundtable"]
    else:
        roster = room["roster"]
        modeOptions = ["Solo", "Roundtable"]

    renderRosterPills(roster)

    leftCol, midCol, rightCol = st.columns([1, 1.2, 1.6])
    with leftCol:
        modeValue = st.radio("Format", modeOptions, horizontal=True, key=modeKey)
    with midCol:
        taskName = st.selectbox("Task", list(room["tasks"].keys()), key=taskKey)
    with rightCol:
        contextDetail = st.text_input(
            room["contextLabel"],
            key=contextKey,
            placeholder=room["contextPlaceholder"],
        )

    isSolo = modeValue == "Solo"
    activeRoster = roster[:1] if isSolo else roster

    messages = st.session_state[messagesKey]

    chosenStarter = None
    if not messages:
        starterCols = st.columns(len(room["starters"]))
        for index, (col, text) in enumerate(zip(starterCols, room["starters"])):
            with col:
                if st.button(text, key=f"starter_{key}_{index}"):
                    chosenStarter = text

    for item in messages:
        renderEntry(item)

    typed = st.chat_input(room["placeholder"], key=f"input_{key}")
    prompt = typed or chosenStarter

    if not prompt:
        return

    if not apiKey:
        st.error("Add a Groq API key in the sidebar to start.")
        return

    userEntry = {"role": "user", "content": prompt, "time": currentTimestamp()}
    messages.append(userEntry)
    renderEntry(userEntry)

    produced = runDeliberation(
        room,
        activeRoster,
        isSolo,
        taskName,
        contextDetail,
        messages,
        apiKey,
        temperature,
        turnBudget,
    )
    if produced == 0:
        messages.pop()


def buildMarkdownExport(room, taskName, contextDetail, roster, messages):
    rosterNames = ", ".join(agentRegistry[key]["name"] for key in roster)
    lines = [
        f"# {appTitle} · {room['label']}",
        "",
        f"- **Task:** {taskName}",
        f"- **Context:** {contextDetail.strip() or 'unspecified'}",
        f"- **Agents:** {rosterNames}",
        f"- **Model:** `{model}`",
        f"- **Exported:** {currentTimestamp()}",
        "",
        "---",
        "",
    ]
    for item in messages:
        lines.extend([f"## {speakerName(item)} · {item['time']}", "", item["content"], "", "---", ""])
    return "\n".join(lines)


def exportFileName(roomKey):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    return f"meridian-{roomKey}-{stamp}.md"


def buildThemeMarkup(accent):
    return f"<style>:root {{ --accent: {accent}; }}\n{themeCss}</style>"


def setActiveRoom(key):
    st.session_state.activeRoom = key


def clearRoom(key):
    st.session_state[f"messages_{key}"] = []


def main():
    st.set_page_config(
        page_title=appTitle,
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "activeRoom" not in st.session_state:
        st.session_state.activeRoom = roomRegistry[0]["key"]

    activeRoom = findRoom(st.session_state.activeRoom)
    activeKey = activeRoom["key"]

    st.markdown(buildThemeMarkup(activeRoom["accent"]), unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f'<div class="brandMark">{appTitle}</div>', unsafe_allow_html=True)
        for room in roomRegistry:
            st.button(
                f"{room['glyph']}   {room['label']}",
                key=f"nav_{room['key']}",
                on_click=setActiveRoom,
                args=(room["key"],),
                type="primary" if room["key"] == activeKey else "secondary",
            )
        st.divider()
        apiKeyInput = st.text_input(
            "Groq API key",
            value=os.environ.get("GROQ_API_KEY", ""),
            type="password",
            help="Used only for requests made in this session.",
        )
        temperature = st.slider("Creativity", 0.0, 1.0, defaultTemperature, 0.05)
        turnBudget = st.slider("Roundtable turns", 2, 12, defaultTurnBudget, 1)
        st.caption(f"Model · {model}")

    renderTicker()
    renderRoom(activeRoom, resolveApiKey(apiKeyInput), temperature, turnBudget)

    with st.sidebar:
        st.divider()
        messages = st.session_state.get(f"messages_{activeKey}", [])
        taskName = st.session_state.get(f"task_{activeKey}", list(activeRoom["tasks"].keys())[0])
        contextDetail = st.session_state.get(f"context_{activeKey}", "")
        exportText = buildMarkdownExport(activeRoom, taskName, contextDetail, currentRoster(activeRoom), messages)
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
            on_click=clearRoom,
            args=(activeKey,),
        )


if __name__ == "__main__":
    main()
