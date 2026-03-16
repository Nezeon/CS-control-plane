# Reference Architecture: Agentic Simulation

> This document explains how the [Agentic_Simulation](https://github.com/Faiziab/Agentic_Simulation) project works.
> It's a reference for how we want to redesign the CS Control Plane's agent system.
> Written in simple language so anyone can understand it.

---

## Table of Contents

**Part 1 — What It Does**
1. [What Is This Project?](#1-what-is-this-project)
2. [All Features](#2-all-features)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [How to Run It](#5-how-to-run-it)

**Part 2 — How It Works Inside**
6. [The 9 Agents](#6-the-9-agents)
7. [The Pipeline (How Work Flows)](#7-the-pipeline-how-work-flows)
8. [Memory System (How Agents Remember)](#8-memory-system-how-agents-remember)
9. [Trait System (Agent Superpowers)](#9-trait-system-agent-superpowers)
10. [Tool System (What Agents Can Do)](#10-tool-system-what-agents-can-do)
11. [Communication System (How Agents Talk)](#11-communication-system-how-agents-talk)
12. [Shared Knowledge & Reflection](#12-shared-knowledge--reflection)

**Part 3 — Dashboard, Config & How We Can Build This**
13. [The Dashboard](#13-the-dashboard)
14. [Configuration Files](#14-configuration-files)
15. [What Gets Saved (Outputs)](#15-what-gets-saved-outputs)
16. [How We Can Build a Similar System](#16-how-we-can-build-a-similar-system)
17. [Key Takeaways](#17-key-takeaways)

---

# Part 1 — What It Does

---

## 1. What Is This Project?

Imagine you have a small R&D department at a company. This department has:
- A **VP** (the boss) who decides the strategy
- **3 team leads** — one for Research, one for Engineering, one for Product
- **3 senior people** — a scientist, an engineer, and a UX researcher
- **2 junior people** — a research analyst and a junior engineer

That's **9 people total**, organized into a real company hierarchy.

Now, this project **replaces all 9 people with AI agents**. Each agent has:
- Its own **personality** (how it talks, thinks, and makes decisions)
- Its own **expertise** (what it's good at)
- Its own **quirks** (habits, catchphrases)
- Its own **memory** (it remembers what happened in previous rounds)
- Its own **tools** (some agents can search the web, do math, read/write files)

When you give the system a prompt like _"Investigate adding AI-powered search to our product"_, the VP breaks it down into tasks, assigns them to the leads, who assign sub-tasks to their team members. Everyone does their part, then results flow back up. The VP synthesizes everything into a final report.

**In simple terms:** It's a simulation of a real team of people — but all powered by AI.

---

## 2. All Features

Here's everything the application can do:

### Agent System
- **9 AI agents** with completely unique personalities, communication styles, and expertise
- **4-level hierarchy**: VP (Level 1) → Department Leads (Level 2) → Senior ICs (Level 3) → Junior ICs (Level 4)
- **3 departments**: Research, Engineering, Product — each with its own mandate
- Every agent stays **in character** throughout the entire simulation (the VP talks like a VP, juniors talk like juniors)

### Processing Pipeline
- **7-round pipeline** that moves work from strategy → planning → execution → review → final report
- **Quality gates** — the VP checks if the work is good enough. If not, it sends agents back to redo their work (up to 2 times)
- **Auto-skip** — rounds that have no work to do are automatically skipped (e.g., if no one asked a cross-department question, the collaboration round is skipped)
- **Hooks** — extra steps like fact-checking and voting that run between rounds

### Memory
- **3-tier memory system**: Working Memory (scratchpad), Episodic Memory (diary), Semantic Memory (textbook)
- Agents **remember** what they did in previous rounds and use those memories to inform their current work
- **Memory consolidation** — old memories get summarized into key insights so the context doesn't get too long
- **Embedding-based retrieval** — when an agent needs to recall something, it searches by meaning (not just keywords)

### Traits (Pluggable Superpowers)
- **9 traits** that can be turned on/off per agent: confidence tracking, voting, skill growth, knowledge graphs, fact-checking, devil's advocate, emotional state, decision logging, stakeholder pressure
- Traits are **plugins** — they hook into the agent's thinking process at specific points (before thinking, after thinking, end of round)

### Tools
- **5 tools** agents can use: web search (Google), read files, write files, list files, calculator
- Tools use **function calling** — the AI model automatically decides when to use a tool and calls it

### Communication
- **Structured message board** — agents send typed messages to each other (task assignments, questions, responses, deliverables, feedback, decisions)
- **Conversation threading** — replies link to the original message, forming threads
- **Priority levels** (low, medium, high, urgent) and **topic tags**
- **Unanswered question tracking** — the system knows if someone hasn't responded yet

### Dashboard
- **Real-time web dashboard** with 8 visualization tabs (live feed, conversations, communication flow, heatmaps, knowledge graph, cross-department tracker, agent profiles, final report)
- Runs at `http://127.0.0.1:8420` when launched with `--live` flag

### Configuration
- **YAML-driven** — you can add new agents, change the pipeline, or enable/disable traits just by editing YAML files. No code changes needed.
- **3 config files**: agent personalities, org structure, pipeline steps

### Outputs & Logging
- Every run produces a **timestamped folder** with: final synthesis, full report, trait reports, activity logs, communication logs, per-agent memory streams, per-agent reflections, department outputs
- All logs are **structured JSONL** (one JSON object per line) — easy to parse and analyze

### Other
- **Tiered models** — different AI models for different hierarchy levels (smarter model for VP, faster model for juniors)
- **Self-reflection** — agents analyze their own performance at the end
- **Shared knowledge pools** — departments share findings that other departments can search
- **Cross-department collaboration** — agents can formally request input from agents in other departments

---

## 3. Tech Stack

| What | Technology | Why |
|------|-----------|-----|
| **AI Brain** | Google Gemini (via `google-genai` SDK) | Powers all agent thinking. Supports function calling (tools) |
| **Language** | Python 3.10+ | The whole project is pure Python |
| **Dashboard** | NiceGUI 3.0+ | Web-based real-time dashboard. Falls back to plain HTML if not installed |
| **Charts** | Plotly 6.0+ | Sankey diagrams (message flow), heatmaps, network graphs |
| **Config** | YAML (via `pyyaml`) | Agent profiles, org structure, and pipeline are all YAML files |
| **Terminal Output** | Rich 13.0+ | Pretty tables, colored output, progress bars in the terminal |
| **Env Management** | python-dotenv | Loads `.env` file for API keys |
| **Embeddings** | Gemini `gemini-embedding-001` | Converts text to vectors for memory retrieval (768 dimensions) |

**Total dependencies: Just 6 Python packages.** The project is intentionally lightweight.

---

## 4. Project Structure

```
Agentic_Simulation/
|
|-- run_simulation.py              # The main entry point. Run this to start.
|-- requirements.txt               # 6 dependencies
|-- README.md                      # User documentation
|-- CLAUDE.md                      # Dev guidance for AI coding assistants
|-- improvements.md                # Research-backed optimization ideas
|
|-- config/                        # ALL configuration lives here (YAML files)
|   |-- agent_profiles.yaml        # 9 agents: personality, traits, tools, expertise
|   |-- org_structure.yaml         # Company hierarchy, departments, reporting lines
|   |-- pipeline.yaml              # 7 rounds + hooks + quality gates
|
|-- simulation/                    # ALL code lives here
|   |-- engine.py                  # THE BRAIN - orchestrates the entire pipeline (1472 lines)
|   |-- agents.py                  # Agent class with cognitive loop (491 lines)
|   |-- communication.py           # Message board system (413 lines)
|   |-- memory.py                  # Working + Episodic + Semantic memory (386 lines)
|   |-- reflection.py              # Self-reflection engine (157 lines)
|   |-- shared_knowledge.py        # Department knowledge pools (233 lines)
|   |-- chat_chains.py             # Multi-turn conversation handler (274 lines)
|   |-- logger.py                  # Structured JSONL logging (255 lines)
|   |-- reporter.py                # Markdown report generation (215 lines)
|   |-- dashboard.py               # Legacy HTML dashboard fallback (1597 lines)
|   |-- ui_dashboard.py            # NiceGUI real-time dashboard (1169 lines)
|   |
|   |-- tools/                     # Tools agents can use
|   |   |-- __init__.py            # Tool registry & resolver
|   |   |-- file_tools.py          # Read/write/list workspace files
|   |   |-- calculator.py          # Safe math calculator
|   |
|   |-- traits/                    # Pluggable agent capabilities
|       |-- __init__.py            # TraitRegistry & BaseTrait base class
|       |-- confidence.py          # Confidence score tracking
|       |-- voting.py              # Voting on proposals
|       |-- skill_growth.py        # Skill development over time
|       |-- knowledge_graph.py     # Building concept networks
|       |-- fact_check.py          # Cross-validating claims
|       |-- devil_advocate.py      # Contrarian arguments (prevents groupthink)
|       |-- emotional_state.py     # Mood/morale tracking
|       |-- decision_log.py        # Tracking decisions made
|       |-- stakeholder_pressure.py # External pressure events (CEO requests, competitor news)
|
|-- runs/                          # Output: one folder per simulation run
|   |-- 2026-02-19_11-18_investigate-the-feasibility.../
|   |   |-- reports/               # Final synthesis + full report + trait reports
|   |   |-- logs/                  # Activity log + communication log (JSONL)
|   |   |-- memory/                # Per-agent memory streams (JSONL)
|   |   |-- reflections/           # Per-agent reflection documents (Markdown)
|   |   |-- departments/           # Per-department output documents
|   |   |-- shared/                # Shared workspace (task board, etc.)
|   |   |-- run_metadata.json      # Run info: prompt, model, duration, status
|
|-- workspace/                     # Live workspace during simulation
|-- docs/                          # Additional documentation
```

**Key insight:** The `config/` folder is separate from the `simulation/` code. This means you can change what the system does (agents, pipeline, traits) without touching any code.

---

## 5. How to Run It

### Basic Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your API key in .env
echo "GOOGLE_API_KEY=your-key-here" > .env

# Run a simulation
python run_simulation.py --prompt "Investigate adding AI-powered search to our product"
```

### All Options

```bash
# Standard run (shows progress in terminal)
python run_simulation.py --prompt "Your prompt here"

# Verbose mode (shows full agent responses)
python run_simulation.py --prompt "..." --verbose

# Live dashboard mode (opens web dashboard at http://127.0.0.1:8420)
python run_simulation.py --prompt "..." --live

# Use a specific model
python run_simulation.py --prompt "..." --model gemini-2.5-pro

# Use tiered models (better model for VP, faster for juniors)
python run_simulation.py --prompt "..." --tiered-models

# List all past simulation runs
python run_simulation.py --list-runs
```

### What Happens When You Run It

1. The system creates a unique run folder (e.g., `runs/2026-02-19_11-18_investigate-the-feasibility/`)
2. It loads all 9 agents from the YAML config files
3. The 7-round pipeline executes:
   - Round 1: VP reads your prompt and breaks it into tasks for each department
   - Round 2: Department leads plan how to handle their tasks
   - Round 3: Team members execute the work (can use tools like web search)
   - Round 3.5: Fact-checking happens (if enabled)
   - Round 4: Cross-department collaboration (agents answer each other's questions)
   - Round 5: Leads review and refine their team's work
   - Quality Gate: VP decides if the work is good enough (loops back if not)
   - Round 5.5: Voting session (if any proposals to vote on)
   - Round 6: Everyone reflects on what they learned
   - Round 7: VP writes the final executive synthesis
4. A comprehensive report is generated
5. All logs, memory, and reflections are saved

**Typical run time:** 2-5 minutes
**API calls per run:** ~30-50 (can go to 100+ if quality gate triggers rework)

---

# Part 2 — How It Works Inside

---

## 6. The 9 Agents

Every agent is defined in `config/agent_profiles.yaml`. Here's who they are:

### The Hierarchy

```
                    Dr. Sarah Chen (VP of R&D)
                    Level 1 - Executive
                    Oversees all departments
                           |
          +----------------+----------------+
          |                |                |
   Dr. James Okafor   Maya Rodriguez    Alex Kim
   Research Lead       Engineering Lead  Product Lead
   Level 2             Level 2           Level 2
          |                |                |
   +------+------+   +----+-----+          |
   |             |    |          |          |
Dr. Priya    Tom    Marcus    Zara      Lena
Sharma       Park   Webb      Ahmed     Voronova
Sr. Scientist Jr.Analyst Sr.Engineer Jr.Engineer UX Researcher
Level 3      Level 4   Level 3     Level 4    Level 3
```

### Agent Details

| Agent | Role | Level | Department | Personality in a Nutshell | Signature Quirk |
|-------|------|-------|------------|--------------------------|-----------------|
| **Dr. Sarah Chen** | VP of R&D | 1 | All | Strategic, decisive, inclusive. Frames everything as impact vs. effort. | Always asks "What's the biggest risk we're not seeing?" |
| **Dr. James Okafor** | Research Lead | 2 | Research | Academic, evidence-based, cautious. Won't recommend without data. | Starts with "The literature suggests..." |
| **Maya Rodriguez** | Engineering Lead | 2 | Engineering | Pragmatic, blunt, prototype-first. Pushes back on scope creep. | Asks "What's the MVP?" in every discussion |
| **Alex Kim** | Product Lead | 2 | Product | Empathetic, user-focused, storyteller. Bridges tech and business. | Says "But what does the user actually need?" |
| **Dr. Priya Sharma** | Sr. Research Scientist | 3 | Research | Deep-diving, perfectionist, thorough to exhaustion. | Adds "Caveat:" before every limitation |
| **Marcus Webb** | Sr. Software Engineer | 3 | Engineering | Reliable, architectural thinker, natural mentor. | Considers the "what if this 10x's" scenario |
| **Lena Voronova** | UX Researcher | 3 | Product | Observant, empathetic, design-thinking approach. | Quotes hypothetical users: "A user might say..." |
| **Tom Park** | Jr. Research Analyst | 4 | Research | Eager, detail-oriented, over-thorough. | Starts with "Quick question..." then writes a lot |
| **Zara Ahmed** | Jr. Software Engineer | 4 | Engineering | Fast learner, practical, action-oriented. | Says "I'll spike on this real quick" |

### What Makes Each Agent Unique

Each agent in `agent_profiles.yaml` has:

```yaml
sarah_chen:
  name: "Dr. Sarah Chen"
  title: "VP of Research & Development"
  level: 1
  department: null  # Oversees all
  personality:
    traits: ["Strategic thinker", "Composed under pressure", ...]
    communication_style: "Concise and structured. Uses numbered lists..."
    decision_approach: "Weighs innovation potential against business reality..."
    expertise: ["R&D strategy", "Cross-functional alignment", ...]
    quirks: ["Always asks 'What's the biggest risk we're not seeing?'", ...]
  traits_enabled: [confidence, voting, skill_growth, knowledge_graph, ...]
  tools_enabled: [google_search, read_workspace_file, list_workspace_files]
```

This personality config gets turned into a **system instruction** that's sent to the AI model with every request. So the AI always stays in character.

### Who Gets What Capabilities

| Capability | VP (L1) | Leads (L2) | Sr. ICs (L3) | Jr. ICs (L4) |
|-----------|---------|------------|--------------|--------------|
| All 9 traits | Yes | Yes | 6 traits | 4 traits |
| Voting | Yes | Yes | No | No |
| Fact-checking | Yes | Yes | No | No |
| Decision logging | Yes | Yes | No | No |
| Devil's advocate | Yes | Yes | Yes | No |
| Stakeholder pressure | Yes | Yes | Yes | No |
| Google search | Yes | Yes | Yes | Yes |
| Calculator | No | Yes | Yes | Yes |
| File read/write | Yes | Yes | Some | No |

The higher your level, the more capabilities you have — just like in a real company.

---

## 7. The Pipeline (How Work Flows)

The pipeline is the heart of the system. It's defined in `config/pipeline.yaml` and runs in this order:

### Round 1: Strategic Decomposition
**Who:** VP (Sarah Chen) only
**What happens:** The VP reads your prompt and breaks it into specific objectives for each department.

Example: If you ask "Investigate adding AI-powered search", the VP might create:
- Research dept: "Analyze state-of-the-art search approaches"
- Engineering dept: "Assess technical feasibility and propose architecture"
- Product dept: "Define user requirements and success metrics"

The VP writes these tasks to a shared task board (`workspace/shared/task_board.md`).

### Round 2: Department Planning
**Who:** Department Leads (James, Maya, Alex)
**What happens:** Each lead reads the VP's objectives and creates specific tasks for their team members.

Example: Research Lead James might assign:
- Priya (Sr. Scientist): "Analyze recent papers on neural search architectures"
- Tom (Jr. Analyst): "Compile competitive analysis of existing search products"

**Runs in parallel** — all 3 leads work at the same time.

### Round 3: Execution
**Who:** All team members (Seniors and Juniors)
**What happens:** Everyone does their assigned work. Agents can:
- Use Google search to look up real information
- Use the calculator for quantitative analysis
- Read/write files in the shared workspace
- Cross-reference memories from earlier rounds

**Runs in parallel** — all ICs work at the same time.

### Round 3.5: Fact-Check Pass (Hook)
**Who:** Agents with the `fact_check` trait (VP + Leads)
**What happens:** These agents review the work produced in Round 3 and flag anything that looks questionable.
**Auto-skips** if no agent has the fact-check trait enabled.

### Round 4: Cross-Department Collaboration
**Who:** Any agents who requested input from other departments
**What happens:** During earlier rounds, agents can write things like:
```
CROSS_DEPT_REQUEST: [marcus_webb] - Need architecture input on search indexing approach
```
In Round 4, Marcus would receive this request and respond.
**Auto-skips** if no cross-department requests were made.

### Round 5: Refinement
**Who:** Department Leads
**What happens:** Leads review all the work from their team, synthesize it, identify gaps, and produce a refined department output.
**Runs in parallel** — all 3 leads work at the same time.

### Quality Gate (between Round 5 and 6)
**Who:** VP (Sarah Chen)
**What happens:** The VP evaluates the quality of all department outputs. Two outcomes:
- **Pass:** Continue to Round 6
- **Fail:** Loop back to Round 3 (Execution) — agents redo their work with the VP's feedback. Can loop up to 2 times.

This is what makes the pipeline "intelligent" — it doesn't just run once. It checks quality and iterates.

### Round 5.5: Voting Session (Hook)
**Who:** Agents with the `voting` trait (VP + Leads)
**What happens:** If there are proposals or decisions to be made, agents vote on them.
**Auto-skips** if no voting is needed.

### Round 6: Reflection & Synthesis
**Who:** All 9 agents
**What happens:** Every agent reflects on what they did, what they learned, and what could be better. Leads also synthesize their team's reflections into higher-level insights.
**Runs in parallel.**

### Round 7: Final Report
**Who:** VP (Sarah Chen) only
**What happens:** The VP reads all department outputs, all reflections, and produces the final executive synthesis. This is the main deliverable of the simulation.

### Pipeline Config Example

```yaml
pipeline:
  - name: "Strategic Decomposition"
    type: round
    round_number: 1
    method: _round_1_strategic_decomposition
    pass_prompt: true            # VP gets the original user prompt

  - name: "Department Planning"
    type: round
    round_number: 2
    method: _round_2_department_planning
    concurrent: true             # Leads work in parallel

  - name: "Quality Gate"
    type: quality_gate
    evaluator: vp
    max_iterations: 2            # Can loop back up to 2 times
    iterate_from: "Execution"    # Where to restart from
```

**Key point:** The entire pipeline is data-driven. You could change the order of rounds, add new ones, or remove hooks — all by editing the YAML file.

---

## 8. Memory System (How Agents Remember)

Think of an agent's memory like your own brain has different types of memory:

### Tier 1: Working Memory (The Scratchpad)

**What it is:** Short-term memory for the current task. Like a whiteboard you're using right now.

**How it works:**
- Holds the last ~20 items (recent context, current task, who assigned it)
- Gets cleared when the task changes
- Passed directly to the AI model in every call

**Think of it as:** The sticky notes on your monitor for today's task.

```python
class WorkingMemory:
    max_items = 20
    current_task = "Analyze search architectures"
    assigned_by = "james_okafor"
    items = ["VP wants to explore AI search", "Focus on vector databases", ...]
```

### Tier 2: Episodic Memory (The Diary)

**What it is:** Everything the agent has experienced — observations, actions, communications, reflections. Each memory has:
- **Content** (what happened)
- **Timestamp** (when)
- **Importance** (1-10 scale — how important is this?)
- **Type** (observation, action, communication, reflection, insight, consolidated)
- **Embedding** (a 768-dimension vector for semantic search)

**How retrieval works:** When an agent needs to recall something, the system uses a **tri-factor scoring** formula:

```
Score = 0.35 * relevance + 0.25 * recency + 0.40 * importance
```

- **Relevance** (35%): How similar is this memory to what I'm looking for? (cosine similarity between embeddings)
- **Recency** (25%): How recent is it? (newer = higher)
- **Importance** (40%): How important was this? (1-10 scale)

So a very important memory from last round scores higher than a random observation from the current round.

**Think of it as:** Your personal diary. You can flip back and find relevant entries based on what you're working on now.

### Tier 3: Semantic Memory (The Shared Textbook)

**What it is:** High-level knowledge shared at the department level. Like a team wiki that everyone can contribute to and search.

**How it works:**
- Each department has a knowledge pool
- Agents **publish** findings (with topic tags)
- Any agent can **query** the pool using semantic search
- Cross-department queries are also supported

**Think of it as:** The team Confluence page where everyone posts their research findings.

### Memory Consolidation

Over time, an agent accumulates hundreds of memories. To prevent the AI from being overwhelmed:

1. After every round, the system checks: do we have 25+ memories?
2. If yes, it takes old memories (more than 2 rounds old)
3. Asks the AI to summarize them into 3 key insights
4. Replaces the old memories with the summary
5. The old memories are still saved on disk (JSONL) — just not in active memory

This keeps the agent's active memory manageable while preserving important knowledge.

---

## 9. Trait System (Agent Superpowers)

Traits are like **plugins** you can attach to agents. Each trait adds special behavior at specific points in the agent's thinking process.

### How Traits Work (Lifecycle Hooks)

Every trait can hook into 5 points in the agent's cognitive loop:

```
1. on_perceive()        -- BEFORE the agent processes new context
                           "Hey agent, also consider THIS extra info"

2. on_think_prompt()    -- BEFORE the agent calls the AI model
                           "Add this extra instruction to your prompt"

3. on_act_postprocess() -- AFTER the agent gets the AI response
                           "Let me enrich/modify your response"

4. on_round_end()       -- AFTER the round finishes
                           "Time to save my state / clean up"

5. on_simulation_end()  -- AFTER the entire simulation is done
                           "Generate my final report"
```

A trait only needs to implement the hooks it cares about. The rest are no-ops (do nothing).

### The 9 Traits Explained

#### 1. Confidence Tracking
**What it does:** Tracks how confident the agent is in its conclusions. Adds qualifiers like "high confidence" or "low confidence" to responses.
**Who has it:** All 9 agents

#### 2. Voting
**What it does:** Enables agents to vote on proposals. When there are competing ideas, agents with this trait can cast votes with reasoning.
**Who has it:** VP + 3 Leads (Level 1-2 only)

#### 3. Skill Growth
**What it does:** Tracks how the agent's skills develop over the simulation. Agents "learn" from their experiences and get better at things they practice.
**Who has it:** All except senior ICs who already have high skills

#### 4. Knowledge Graph
**What it does:** Builds a network of concepts and relationships. As the agent learns things, it connects them (e.g., "vector search → requires embeddings → needs GPU infrastructure").
**Who has it:** All except senior ICs

#### 5. Fact-Check
**What it does:** Cross-validates claims made by other agents. If someone says "GPT-4 is 95% accurate on this task," the fact-checker will verify that.
**Who has it:** VP + 3 Leads (Level 1-2 only)

#### 6. Devil's Advocate
**What it does:** Intentionally argues the opposite side to prevent groupthink. The intensity scales with seniority — VP pushes back harder than a senior IC.
**Who has it:** All except juniors (Levels 1-3)

#### 7. Emotional State
**What it does:** Tracks the agent's mood/morale on a scale of 0.0 to 1.0. Praise improves mood, criticism lowers it. Mood affects communication style.
**Who has it:** All 9 agents

#### 8. Decision Log
**What it does:** Automatically extracts decisions from agent responses and maintains a running log. Injects the decision history into future prompts so agents don't contradict themselves.
**Who has it:** VP + 3 Leads (Level 1-2 only)

#### 9. Stakeholder Pressure
**What it does:** Injects external events like "CEO wants a status update by Friday" or "Competitor just launched a similar feature." Creates realistic pressure.
**Who has it:** All except juniors (Levels 1-3)

### How to Add a New Trait

1. Create a file: `simulation/traits/my_new_trait.py`
2. Implement the `BaseTrait` class with the hooks you need
3. Register it in `simulation/traits/__init__.py`
4. Enable it per agent in `config/agent_profiles.yaml`

That's it. No other code changes needed.

---

## 10. Tool System (What Agents Can Do)

Tools let agents interact with the outside world. The system uses **Gemini's function calling** — the AI model decides when it needs a tool and calls it automatically.

### Available Tools

| Tool | Type | What It Does | Example |
|------|------|-------------|---------|
| **google_search** | Native Gemini | Searches the web for real information | Agent searches for "latest vector database benchmarks 2025" |
| **read_workspace_file** | Custom Python | Reads a file from the shared workspace | Agent reads another team's output: `departments/engineering/output.md` |
| **write_workspace_file** | Custom Python | Writes a file to the shared workspace | Agent saves their analysis to `departments/research/nlp_analysis.md` |
| **list_workspace_files** | Custom Python | Lists all files in the workspace | Agent checks what outputs exist from other teams |
| **calculator** | Custom Python | Evaluates math expressions safely | Agent calculates `sqrt(1024 * 768) / 2` for a performance estimate |

### How Tool Integration Works

1. Agent profiles define which tools each agent can use:
   ```yaml
   tools_enabled: [google_search, calculator, read_workspace_file]
   ```

2. The `resolve_tools()` function converts these names into Gemini-compatible objects

3. When the agent calls the AI model, the tools are passed along:
   ```python
   response = client.models.generate_content(
       model=self.model_name,
       contents=prompt,
       config={
           "system_instruction": self.system_instruction,
           "tools": tools_list,  # <-- tools available to the model
       }
   )
   ```

4. Gemini automatically decides if/when to use a tool. If it does, the SDK executes the function and feeds the result back to the model.

5. Tool usage is tracked in agent memory and shown in the dashboard.

### Who Can Use What

- **VP (Sarah Chen):** Google search, read files, list files (can see everything, but doesn't write)
- **Leads (James, Maya, Alex):** Google search, read files, list files, calculator
- **Seniors (Priya, Marcus):** Google search, calculator (+ read files for Marcus)
- **Juniors (Tom, Zara):** Google search, calculator (limited access)

---

## 11. Communication System (How Agents Talk)

Agents don't just think in isolation — they communicate through a centralized **message board**.

### Message Structure

Every message has:
```
from_agent: "james_okafor"          # Who sent it
to_agent: "priya_sharma"            # Who it's for (or "all" for broadcast)
content: "Analyze recent NLP papers" # The actual message
msg_type: "task_assignment"         # What kind of message
channel: "direct"                   # How it's routed
priority: "high"                    # How urgent
tags: ["NLP", "search"]             # Topic tags
thread_id: "msg_0001"              # Conversation thread
requires_response: true             # Sender expects a reply
```

### Message Types

| Type | When Used | Example |
|------|----------|---------|
| `task_assignment` | Lead assigns work to team member | "Analyze search architectures" |
| `question` | Anyone asks another agent something | "What's the latency of vector search?" |
| `response` | Reply to a question | "Based on benchmarks, around 10ms for 1M vectors" |
| `deliverable` | Submitting completed work | "Here's my analysis of search approaches" |
| `escalation` | Raising an issue to a higher level | "We found a blocker — need VP input" |
| `feedback` | Reviewing someone's work | "Good analysis, but add more on cost" |
| `decision` | Recording a formal decision | "We've decided to use vector search" |

### How Communication Flows

```
VP (Sarah Chen)
  |
  |-- [task_assignment] --> Research Lead (James)
  |-- [task_assignment] --> Engineering Lead (Maya)
  |-- [task_assignment] --> Product Lead (Alex)

James:
  |-- [task_assignment] --> Priya (Sr. Scientist)
  |-- [task_assignment] --> Tom (Jr. Analyst)

Priya:
  |-- [deliverable] --> James (sends back her work)
  |-- [question] --> Marcus (cross-dept: "What infra do we need?")

Marcus:
  |-- [response] --> Priya (answers the question)

James:
  |-- [deliverable] --> Sarah (refined department output)
```

Tasks flow **down** the hierarchy. Deliverables flow **up**. Questions go **sideways** (cross-department).

### Threading

When Priya asks Marcus a question, and Marcus replies, those messages are linked by `thread_id`. The system can:
- Show the full conversation thread
- Track if questions are answered or still pending
- Inherit topic tags from parent messages

### Unanswered Question Tracking

The system knows if someone hasn't responded to a question:
```python
unanswered = message_board.get_unanswered("marcus_webb")
# Returns: [Message(from=priya, "What infra do we need?")]
```

This is used to ensure cross-department collaboration actually happens in Round 4.

---

## 12. Shared Knowledge & Reflection

### Shared Knowledge Pools

Each department has a shared knowledge pool — like a team wiki.

**How it works:**
1. An agent discovers something important during their work
2. They publish it to their department's knowledge pool:
   ```python
   knowledge_manager.publish_to_dept(
       department="research",
       agent_id="priya_sharma",
       content="Vector search with HNSW index achieves 10ms latency at 1M scale",
       tags=["vector-search", "performance"],
       importance=8,
   )
   ```
3. Any agent in the Research department can query this knowledge:
   ```python
   results = knowledge_pool.query("search performance benchmarks")
   ```
4. Cross-department queries also work:
   ```python
   results = knowledge_manager.cross_dept_query(
       query="search architecture options",
       source_dept="engineering",  # Don't search own department
   )
   ```

**Search uses embeddings** — so it finds things by meaning, not just keywords. Searching for "How fast is vector search?" would find the entry about "10ms latency at 1M scale."

### Self-Reflection

At the end of the simulation (Round 6), every agent reflects on their experience. The system asks them:

1. **Salient Questions** — What are the biggest open questions from this work?
2. **Insights** — What patterns do you see? What connections can you make?
3. **Self-Assessment** — What went well? What could you do better?

For **leads and the VP**, reflection goes a step further — they also synthesize their team's reflections:

1. **Cross-Cutting Themes** — What patterns emerge across the team?
2. **Alignment & Conflicts** — Where does the team agree? Where are there tensions?
3. **Strategic Insights** — What can you see that no individual could see alone?
4. **Recommendations** — What should we focus on next?
5. **Risk Assessment** — What blind spots has the team missed?

Reflections are stored back into memory as high-importance entries (importance=8-9), so they influence future work if the pipeline loops.

### Reflection is Triggered by Importance

Reflection doesn't happen randomly. The system checks: has the agent accumulated enough "important stuff" since the last reflection?

```python
REFLECTION_THRESHOLD = 25  # Cumulative importance score

# If sum of importance scores since last reflection >= 25, reflect
if cumulative_importance >= 25:
    trigger_reflection()
```

This means agents who did a lot of important work reflect more deeply, while agents who had simple tasks may produce lighter reflections.

---

# Part 3 — Dashboard, Config & How We Can Build This

---

## 13. The Dashboard

When you run the simulation with `--live`, a real-time web dashboard opens at `http://127.0.0.1:8420`. It has **8 tabs**:

### Tab 1: Live Feed
**What it shows:** A real-time scrolling feed of everything happening — which agent is thinking, what they're doing, tool calls, messages sent.
**Think of it as:** A Slack-like activity feed for the simulation.

### Tab 2: Conversations
**What it shows:** Agent outputs organized by round. You can expand each agent to see their full response.
**Think of it as:** Meeting notes grouped by session.

### Tab 3: Communication Flow (Sankey Diagram)
**What it shows:** A Plotly Sankey diagram showing who talked to who, how many messages, and what types.
**Think of it as:** A visual map of "who is collaborating with who."
- Left side: senders
- Right side: receivers
- Thickness of the line = number of messages

### Tab 4: Confidence Heatmap
**What it shows:** A grid where rows are agents and columns are rounds. Color shows confidence level.
**Think of it as:** A heat map showing how confident each agent was at each stage.

### Tab 5: Knowledge Graph
**What it shows:** A network visualization of concepts and how they connect. Built from the knowledge_graph trait.
**Think of it as:** A mind map that the agents built together.

### Tab 6: Cross-Department Tracker
**What it shows:** All cross-department requests — who asked who, what they asked, whether it's been answered.
**Think of it as:** A project tracker for inter-team collaboration.

### Tab 7: Agent Profiles
**What it shows:** Each agent's stats — how many memories, how many messages sent/received, tool usage, skill levels.
**Think of it as:** A player stats card for each agent.

### Tab 8: Report
**What it shows:** The final markdown report rendered nicely in the browser.
**Think of it as:** The final deliverable, readable right in the dashboard.

### Dashboard Design
- **Theme:** Dark glassmorphism (dark background, frosted glass panels)
- **Background:** #060a13 (very dark, almost void-like)
- **Fonts:** Inter (UI), JetBrains Mono (code/data)
- **Updates:** Real-time — the dashboard refreshes as agents work
- **Token/cost tracking:** Shows total API tokens used and estimated cost in the header

### Fallback
If NiceGUI isn't installed, the system falls back to a legacy HTML dashboard (`dashboard.py`, 1597 lines) with basic visualization. The simulation still works fine — you just don't get the fancy UI.

---

## 14. Configuration Files

The entire system is configured through 3 YAML files. **No code changes needed** to customize the simulation.

### File 1: `config/agent_profiles.yaml` — Who The Agents Are

Controls:
- Agent names, titles, levels, departments
- Complete personality (traits, communication style, decision approach, expertise, quirks)
- Which traits are enabled per agent
- Which tools are enabled per agent

**To add a new agent:** Just add a new entry in this file with a personality, enable traits, and add them to the org structure.

### File 2: `config/org_structure.yaml` — How The Team Is Organized

Controls:
- Company name and division
- 4 hierarchy levels with descriptions
- 3 departments with mandates
- Who reports to who (reporting lines)
- Team composition (who is in which department)

**To add a new department:** Add a department entry with a head, members, and mandate. Then add reporting lines for the new members.

### File 3: `config/pipeline.yaml` — What Steps To Execute

Controls:
- The sequence of rounds, hooks, and quality gates
- Which engine method each step calls
- Whether steps run in parallel (`concurrent: true`)
- Whether steps auto-skip when there's no work (`auto_skip: true`)
- Quality gate settings (who evaluates, max iterations, where to loop back to)
- Whether the original prompt gets passed to a step (`pass_prompt: true`)

**To change the pipeline:** Edit this file. You can reorder rounds, add new ones, remove hooks, or change quality gate behavior.

---

## 15. What Gets Saved (Outputs)

Every simulation run creates a timestamped folder. Here's what's inside:

```
runs/2026-02-19_11-18_investigate-the-feasibility/
|
|-- run_metadata.json           # Run info
|   {
|     "prompt": "Investigate adding AI-powered search...",
|     "model": "gemini-2.5-flash",
|     "started_at": "2026-02-19T11:18:23",
|     "completed_at": "2026-02-19T11:21:47",
|     "duration_seconds": 204.3,
|     "status": "completed"
|   }
|
|-- reports/
|   |-- final_synthesis.md      # VP's executive summary (the main deliverable)
|   |-- simulation_report.md    # Full multi-round report with all outputs
|   |-- trait_reports.md        # Confidence scores, voting results, skill growth
|
|-- logs/
|   |-- activity_log.jsonl      # Every agent action with metadata (one JSON per line)
|   |-- communication_log.jsonl # Every message between agents (one JSON per line)
|
|-- memory/
|   |-- sarah_chen.jsonl        # VP's memory stream
|   |-- james_okafor.jsonl      # Research Lead's memory
|   |-- maya_rodriguez.jsonl    # Engineering Lead's memory
|   |-- ... (one file per agent, 9 total)
|
|-- reflections/
|   |-- sarah_chen_reflection.md     # VP's self-reflection
|   |-- james_okafor_reflection.md   # Research Lead's reflection
|   |-- ... (one file per agent, 9 total)
|
|-- departments/
|   |-- research/department_output.md    # Research team's final output
|   |-- engineering/department_output.md # Engineering team's final output
|   |-- product/department_output.md     # Product team's final output
|
|-- shared/
    |-- task_board.md           # VP's strategic decomposition
```

**Everything is human-readable** — markdown for reports, JSONL for logs (one JSON per line, easy to parse).

---

## 16. How We Can Build a Similar System

Here's how the reference architecture maps to our CS Control Plane. We need changes in both **backend** and **frontend**.

### Backend Changes

| What the Reference Has | What We Currently Have | What We Need To Change |
|------------------------|----------------------|----------------------|
| **YAML agent profiles** with personality, traits, tools | Hardcoded `AGENT_REGISTRY` dict in `routers/agents.py` — agents are just name/description strings | Create YAML config files for our 10 CS agents. Each agent gets a personality, expertise, enabled traits, enabled tools. Load from YAML at startup. |
| **7-round pipeline** (strategy → planning → execution → review → synthesis) with quality gates | **Single-shot execution** — trigger an agent, it runs once, done | Build a pipeline engine that runs agents in sequence across multiple rounds. Add quality gates where the Orchestrator evaluates output quality and can request rework. |
| **3-tier memory** (working + episodic + semantic) with embedding-based retrieval | Basic DB queries in Memory Agent — just pulls customer data from PostgreSQL | Add working memory (per-pipeline context), episodic memory (agent action history with embeddings in ChromaDB), and semantic memory (shared knowledge pools). Use tri-factor retrieval. |
| **9 pluggable traits** with lifecycle hooks (on_perceive, on_think, on_act, on_round_end) | No trait system at all | Create a trait registry with lifecycle hooks. Implement traits relevant to CS: confidence tracking, decision logging, escalation detection, customer sentiment awareness. |
| **Tool system** — agents call functions (search, calculate, read/write files) via LLM function calling | No tool integration — agents just get a prompt and return text | Add a tool registry. Enable Claude `tool_use` for our agents. Relevant tools: query customer DB, search past tickets (RAG), check health scores, create Jira ticket, send Slack message. |
| **Structured message board** with threading, priorities, tags | No inter-agent messaging — agents don't communicate with each other | Add a communication system. When the pipeline runs, agents can post messages to each other (e.g., Health Monitor flags risk → Escalation agent picks it up). |
| **Structured JSONL logging** — every action, every message, per-agent memory | Basic `agent_logs` table in PostgreSQL | Add detailed JSONL logging. Log every LLM call, every tool use, every message, every memory retrieval. Store in both DB and files. |
| **Reflection engine** — agents self-assess after completing work | No self-reflection | Add a reflection step at the end of multi-step pipelines. Agents analyze their work quality and generate insights for next time. |
| **Pipeline YAML config** — round sequence is data-driven | Hardcoded orchestrator routing (event type → agent mapping in a Python dict) | Make pipeline steps configurable via YAML. Different event types can trigger different pipelines (e.g., "new ticket" pipeline vs. "health alert" pipeline). |

### Frontend Changes (New React Build)

The reference repo uses NiceGUI for its dashboard. We'll build equivalent features in React.

| Reference Dashboard Feature | What We'll Build in React |
|----------------------------|--------------------------|
| **Live Feed** — real-time scrolling activity stream | WebSocket-powered agent activity feed. Show which agent is thinking, what tool it's using, results in real-time. |
| **Conversations** — agent outputs grouped by round | Pipeline execution viewer. Show each step's output, expandable per agent. Like a step-by-step debugger for the pipeline. |
| **Communication Flow (Sankey)** — who talked to who | Inter-agent message flow visualization. Use D3 or Recharts to show message routing between agents. |
| **Confidence Heatmap** — agent confidence per round | Agent performance heatmap. Show confidence, response quality, or processing time per agent per pipeline step. |
| **Knowledge Graph** — concept network | Knowledge network visualization. Show how customer knowledge, tickets, and insights connect. Could use Three.js for 3D. |
| **Cross-Department Tracker** — collaboration status | Cross-agent collaboration view. Show which agents requested help from other agents and whether it was fulfilled. |
| **Agent Profiles** — stats per agent | Agent detail cards. Show each agent's capabilities, recent activity, success rate, tool usage stats. |
| **Report** — rendered final report | Pipeline output viewer. Show the final synthesized result in a nice readable format. |

### Key Architecture Differences

| Aspect | Reference (Agentic Simulation) | Our CS Control Plane |
|--------|-------------------------------|---------------------|
| **LLM** | Google Gemini | Claude (Anthropic) |
| **Storage** | JSONL files on disk | PostgreSQL + ChromaDB (already have both) |
| **Persistence** | Per-run files | Database (persistent across runs) |
| **Trigger** | Manual CLI command | Event-driven (Jira webhooks, cron jobs, API calls) |
| **Frontend** | NiceGUI (Python) | React (JavaScript) — much richer UI |
| **Real-time** | NiceGUI state updates | WebSocket (already have this) |
| **Agents** | 9 R&D department agents | 10 CS workflow agents |
| **Use case** | One-shot R&D analysis | Ongoing customer success automation |

---

## 17. Key Takeaways

The most important lessons from the reference architecture:

### 1. Agents Need Personality
Don't just give agents a role — give them a full personality with communication style, decision approach, expertise, and quirks. This makes their outputs more distinct and useful. **Our agents currently have no personality — they just execute a prompt.**

### 2. Pipeline Over Single-Shot
A multi-round pipeline with quality gates produces much better results than single-shot execution. The VP can catch issues and send work back for revision. **Our agents currently run once and produce whatever they produce — no review loop.**

### 3. Memory Makes Agents Smart
The 3-tier memory system (working + episodic + semantic) with embedding-based retrieval is what makes agents "remember" and improve. Without it, every run starts from scratch. **Our Memory Agent just pulls customer data from the DB — there's no actual agent memory system.**

### 4. Traits Make Agents Extensible
The plugin trait system means you can add capabilities without changing core code. Need fact-checking? Add a trait. Need voting? Add a trait. **We have no trait system — adding capabilities means editing agent code.**

### 5. Tools Make Agents Useful
Agents that can use tools (search, read files, query databases) produce grounded, factual outputs. Without tools, they can only hallucinate. **Our agents currently have no tools — they get a text prompt and return text.**

### 6. Communication Enables Collaboration
Agents that can talk to each other discover things no single agent could find alone. Cross-department collaboration is where the real value emerges. **Our agents are completely isolated — they never communicate with each other.**

### 7. YAML Config Makes Everything Flexible
Moving agent definitions, pipeline steps, and trait assignments to YAML files makes the system incredibly flexible. You can add agents, change the pipeline, or tweak behavior without writing code. **Our agents are hardcoded in Python files and a dict in the router.**

### 8. Reflection Improves Quality
When agents reflect on their work, they catch their own mistakes and generate insights. Leads synthesizing team reflections produces even higher-level understanding. **Our agents have no self-assessment capability.**

### 9. Structured Logging Enables Debugging
JSONL logging of every action, message, and memory makes it possible to understand exactly what happened and why. **Our logging is minimal — just basic agent_logs entries.**

### 10. The Separation of Config and Code
The reference project cleanly separates "what the system does" (YAML config) from "how it does it" (Python code). This is the key architectural principle we should adopt.

---

> **Next step:** Use this document as the blueprint for redesigning the CS Control Plane's backend agent system and building a new React frontend to visualize the pipeline, memory, and inter-agent communication.

