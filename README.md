# AetherMed // Multi-Agent Pathology Interpreter

**Track:** Agents for Good  
**Type:** Responsive Web Application  
**Code Limit:** Under 2,500 lines of code (~1,300 lines total)

AetherMed is an intelligent patient-facing workspace that translates complex, unstructured clinical blood test reports into clear, empathetic, and actionable insights. By coordinating multiple virtual agents, it helps patients understand their health markers, flags out-of-range anomalies against standard reference levels, and suggests appropriate specialists alongside critical consultation questions.

---

## Demonstrated Key Concepts in Code

Rather than requiring video demonstrations, this repository showcases three advanced agentic concepts directly in clean, readable code:

### 1. Multi-Agent System (ADK Integration)
The application coordinates a sequential pipeline of 4 specialized python agents located in [`backend/agents/`](file:///d:/ai%20agent/captsone%20project/backend/agents):
* **Extractor Agent (`agent1_extractor.py`):** Parses messy, unstructured clinical text input and structures it into standardized JSON key-value pairs.
* **Analyzer Agent (`agent2_analyzer.py`):** Takes extracted values and checks them against standard reference ranges sourced directly from the local MCP server.
* **Explainer Agent (`agent3_explainer.py`):** Decodes out-of-range clinical markers into warm, jargon-free, layperson explanations without introducing anxiety.
* **Recommender Agent (`agent4_recommender.py`):** Identifies the clinical specializations relevant to flagged anomalies and prepares a printable checklist of questions for the patient's next appointment.

### 2. Model Context Protocol (MCP) Server
To guarantee precision and prevent LLM hallucinations, the Analyzer Agent leverages a local **MCP Server** (`mcp_server/server.py`). Exposing tools over SSE (Server-Sent Events), the MCP server queries a local JSON database of clinical reference ranges. If the MCP server is offline, the system falls back gracefully to secondary local tables.

### 3. Security & PII Redactor
To protect patient privacy, a dedicated local PII security engine (`backend/security.py`) intercepts all inputs. It automatically scrubs names, dates of birth, contact details (phone, email), and identification numbers using advanced pattern-matching *before* the data is processed by the agent pipeline.

---

## Codebase Architecture & File Structure

```
d:\ai agent\captsone project\
├── frontend/
│   ├── index.html           # Premium glassmorphic workspace layout
│   ├── style.css            # Custom CSS styling & timeline/processing transitions
│   └── app.js               # Event controller and async API pipeline renderer
├── backend/
│   ├── main.py              # FastAPI orchestration server & endpoints
│   ├── config.py            # Environment loader (loads .env configuration)
│   ├── security.py          # Security utility containing local PII redactor
│   └── agents/
│       ├── base.py          # Shared Agent wrapper (Gemini configuration + Simulation fallback)
│       ├── agent1_extractor.py  # Structured extractor
│       ├── agent2_analyzer.py   # MCP-integrated clinical range comparison engine
│       ├── agent3_explainer.py  # Patient jargon explainer
│       └── agent4_recommender.py# Consultation roadmap and questions compiler
├── mcp_server/
│   ├── server.py            # FastMCP server exposing tools and resources
│   └── data/
│       └── reference_ranges.json # Standard clinical reference ranges database
├── .env.example             # Environment template
├── .env                     # Local environment settings
├── requirements.txt         # Package dependencies
└── run.py                   # Universal multi-process service orchestrator
```

---

## Quick Start: Run Locally

### 1. Prerequisites
Make sure you have **Python 3.10+** installed on your system.

### 2. Installation
Clone the repository and install the dependencies listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
By default, the application runs in a **high-fidelity simulation/mock mode** so you can test it instantly without an API key. 

If you want to use the live Gemini LLM, edit the `.env` file in the root directory:
```env
USE_GEMINI_API=true
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Launching the Services
Start all servers (FastAPI backend, MCP Server, and Frontend Web server) using the unified launcher script:
```bash
python run.py
```

This will spin up:
* **Frontend Dashboard** at `http://localhost:8080`
* **FastAPI Orchestrator** at `http://localhost:8000`
* **MCP Server** at `http://localhost:8001`

Open [http://localhost:8080](http://localhost:8080) in your browser to interact with the workspace!

---

## Interactive Features & UX
1. **Status Indicators:** The top header displays live status dots checking connections to the backend, the MCP Range Server, and the Gemini API mode.
2. **Presets Loading:** Instantly test different scenarios (Healthy Complete Blood Count, Anemic Complete Blood Count, or Diabetic Basic Metabolic Panel) by clicking preset buttons.
3. **Animated Pipeline Timeline:** Watch the agents collaborate step-by-step. The interface highlights the active agent with glowing indicators and details the action performed and the duration.
4. **Scrubbed Raw Data:** Review the outputs in the workspace tabs to confirm that patient identifying names, addresses, and numbers have been completely redacted before analysis.
5. **Parameter Checks Table:** Displays the extracted results formatted in a clean table with dynamic status tags (Normal, Low, High).
