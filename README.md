# Meridian Toolbox

A multi-agent AI workspace built with Streamlit and powered entirely by Groq. Seven domain rooms and a cross-disciplinary Council give you single assistants for focused work, or a roundtable of specialist agents that debate, challenge, and refer to each other by name.

Everything lives in one file, `meridian_toolbox.py`.

## Features

### Rooms

| Room | Agents | What it's for |
|---|---|---|
| **General** | Atlas, Sable | Conversation, summaries, rewrites, brainstorming, planning |
| **Mathematics** | Euler, Sable, Atlas | Solving problems, explaining concepts, checking proofs, practice sets, estimates |
| **Science** | Curie, Sable, Euler | Mechanisms, experiment design, data analysis, study critiques, units |
| **Languages** | Babel, Atlas, Sable | Translation, correction, conversation practice, grammar, drills |
| **History** | Clio, Sable, Metternich | Timelines, source analysis, causal comparison, counterfactuals |
| **Geopolitics** | Metternich, Clio, Sable | Briefings, stakeholder maps, scenario analysis, treaty explainers, steelmen |
| **Environmental** | Gaia, Curie, Atlas, Sable | Impact assessments, carbon estimates, climate explainers, action plans |
| **Council** | Any agents you seat | Debates, joint research briefs, red-teaming plans, decision memos |

### Agents

| Agent | Role | Persona |
|---|---|---|
| Atlas | Generalist synthesizer | Pragmatic, turns discussions into next steps |
| Euler | Mathematician | Rigorous, demands definitions and checks every step |
| Curie | Experimental scientist | Evidence-first, asks what would falsify a claim |
| Babel | Linguist | Attentive to register and idiom, notices what translation loses |
| Clio | Historian | Source-minded, warns against anachronism |
| Metternich | Geopolitical strategist | Thinks in interests, leverage, and constraints |
| Gaia | Environmental scientist | Systems-minded, weighs ranges and tradeoffs |
| Sable | Red-team skeptic | Challenges weak claims and hidden assumptions |
| Nexus | Moderator | Closes each roundtable with agreements, disagreements, and a recommendation |

### Solo and Roundtable formats

- **Solo** sends your prompt to a single agent, the first in the room's roster.
- **Roundtable** runs a live discussion. Agents take turns, each one reading the whole conversation so far. They refer to each other with `@Name`, and those mentions are highlighted. An agent can also hand off to a colleague by ending its turn with `[[ask: Name]]`, which moves that colleague to the front of the queue. When the turn budget runs out, Nexus writes a closing synthesis.

The **Roundtable turns** slider in the sidebar (2 to 12) sets how many agent turns run before Nexus closes. Moderator turns don't count against it.

### Exporting

Each room keeps its own history. The **Export this room (.md)** button downloads a Markdown file with the task, context, agent list, model, timestamp, and every message labeled by speaker. Markdown and LaTeX in the messages render as they do on screen.

## Requirements

- Python 3.9 or newer
- A Groq API key
- The packages in `requirements.txt`

## Installation

```bash
git clone <your-repo-url> meridian-toolbox
cd meridian-toolbox
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

The app needs a Groq API key. You can provide it in either of two ways:

1. Export it as an environment variable before launching:

   ```bash
   export GROQ_API_KEY="your_key_here"        # Windows PowerShell: $env:GROQ_API_KEY="your_key_here"
   ```

2. Paste it into the **Groq API key** field in the sidebar. The key is used only for requests made in the current session.

The model is fixed in the source as `openai/gpt-oss-120b`. To change it, edit the `model` variable near the top of `meridian_toolbox.py`.

## Running

```bash
streamlit run meridian_toolbox.py
```

Streamlit prints a local URL, usually `http://localhost:8501`. Open it in a browser.

## Usage

1. Pick a room from the sidebar.
2. Choose **Solo** or **Roundtable**, a task, and optionally a context such as the audience or level.
3. Start with one of the starter prompts or type your own in the chat box.
4. In Council, use the **Agents at the table** selector to choose who participates before you send a message.
5. Export the room with the sidebar button when you want to keep the transcript.

Each room has its own history, so switching rooms does not lose the conversation in another one. **Clear this room** erases only the room you're viewing.

## Project structure

```
meridian-toolbox/
├── meridian_toolbox.py   # The entire application
├── requirements.txt      # Python dependencies
└── README.md
```

The file is organized top to bottom as: configuration, agent and room registries, CSS theme, prompt construction, Groq streaming, the deliberation loop, rendering, and the `main()` entry point.

## Extending

**Add a room.** Append a dict to `roomRegistry` with `key`, `label`, `glyph`, `accent`, `tagline`, `contextLabel`, `contextPlaceholder`, `placeholder`, `roster`, `tasks`, and `starters`. Each entry in `tasks` maps a task name to the instruction the agents receive. The new room appears in the sidebar automatically.

**Add an agent.** Add an entry to `agentRegistry` with `name`, `role`, `emoji`, `tone`, and `persona`. Add its key to any room's `roster`, or select it in Council. Agents are referred to by name, so keep names unique and single-word, since the `[[ask: Name]]` parser matches one word.

**Change the look.** Colors come from each room's `accent` and each agent's `tone`. The full stylesheet is in the `themeCss` string.

## Troubleshooting

- **"Add a Groq API key in the sidebar to start."** Set `GROQ_API_KEY` or paste the key into the sidebar field.
- **"Groq request failed" in a chat.** Check the key, your network connection, and the Groq service status. The failed message is removed from the history so you can resend it.
- **Styling looks off or the sidebar behaves oddly.** The CSS targets Streamlit's internal test IDs such as `stChatMessage` and `stBaseButton-primary`. Upgrade or pin Streamlit to a version that works with the stylesheet.
- **Roundtables are slow.** Each turn is a separate model call made in sequence. Lower the **Roundtable turns** slider or use Solo for quick answers.
- **Council says to seat an agent.** Select at least one agent in the **Agents at the table** field.

## Limitations

- Conversation history lives in the browser session and is lost when the session ends. Export a room to keep it.
- The model cannot browse the web. Answers reflect its training data, and the agents are instructed not to invent citations, but you should verify important facts.
- Agents are language-model personas, not credentialed experts. Treat their output as a starting point for your own judgment.

## License

Add your license here.
