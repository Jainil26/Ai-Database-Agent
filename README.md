# 🤖 Agent Jarvis — Autonomous AI Database Agent

A fully autonomous AI Database Agent built from scratch using **pure Python** — no LangChain, no CrewAI, no drag-and-drop frameworks. Just raw agent architecture: a reasoning loop, custom tools, memory management, and a conversational web UI.

Built during a software development internship over 16 days.

---

## 🧠 How It Works

Most people build "AI agents" by chaining API calls or dragging nodes on n8n. This project builds the real thing — from the ground up.

```
User Message
     │
     ▼
 Reasoning Loop  ◄─────────────────────┐
     │                                  │
     ▼                                  │
Tool Selection (JSON Schema)            │
     │                                  │
     ▼                                  │
Tool Execution                          │
  ├── ask_database()  → MySQL           │
  ├── create_file()   → Local FS        │
  ├── read_file()     → Local FS        │
  └── get_time()      → System          │
     │                                  │
     ▼                                  │
Observe Result ────────────────────────►┘
     │
     ▼ (task complete)
 Final Response → Chainlit UI
```

The agent keeps looping — calling tools, observing results, deciding next steps — until the task is fully complete. No human in the loop.

---

## 🏗️ Project Structure

```
Database Agent/
│
├── .chainlit/
│   ├── translations/
│   └── config.toml
│
├── .files/
│   └── .env                  # API keys and DB credentials (not committed)
│
├── .gitignore
├── chainlit.md               # Chainlit welcome screen content
├── database_agent.py         # Core agent — reasoning loop, tools, memory, UI
├── schema_prompt.py          # MySQL schema definitions and SQL rulebook
└── README.md
```

---

## ⚙️ Features

- **Inner Autonomous Loop** — Agent calls tools back-to-back without human intervention until the task is done
- **6 Custom Tools** with full JSON schemas registered via the OpenRouter tool-calling API:
  - `ask_database` — Translates natural language → SQL → executes on MySQL (sub-agent pattern)
  - `create_file` — Creates and writes local text files
  - `read_file` — Reads local file contents
  - `get_time` — Fetches current system timestamp
  - `say_hello` — Greeting function
  - `get_agent_name` — Returns agent identity
- **Sub-Agent Pattern** — `ask_database()` runs its own internal LLM call to generate SQL before touching MySQL
- **Sliding Window Memory** — Conversation history capped at 20 turns to stay within context limits
- **Custom JSON Encoder** — Handles MySQL `Decimal` and `datetime` types that standard `json.dumps()` cannot serialize
- **Chainlit Web UI** — Dark-themed conversational interface with real-time multi-turn support

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| LLM Provider | OpenRouter (`nvidia/nemotron` / `openrouter/free`) |
| SQL Generation | Gemini API (`google-genai`) |
| Database | MySQL via `pymysql` |
| Web UI | Chainlit |
| Environment | `python-dotenv` |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Jainil26/Ai-Database-Agent.git
cd Ai-Database-Agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file inside the `.files/` folder:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
DB_HOST=localhost
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
```

### 4. Set up the MySQL database

Run your schema setup script in MySQL Workbench or via CLI. The agent expects these tables:

```sql
categories (category_id, name)
products (product_id, category_id, product_name, status)
product_variants (variant_id, product_id, sku, price)
customers (customer_id, first_name, last_name, email)
orders (order_id, customer_id, order_status, total_amount)
```

### 5. Run the agent

**Web UI mode (Chainlit):**
```bash
chainlit run database_agent.py
```

Then open `http://localhost:8000` in your browser.

---

## 🐛 Real Bugs Solved

These are actual issues hit during development — not hypothetical:

| Bug | Cause | Fix |
|---|---|---|
| Infinite loop | `cursor.fetchall` missing `()` — referenced, never called | Added parentheses to execute the function |
| JSON crash | MySQL returns `Decimal` objects for financial fields | Built `DatabaseJsonEncoder` class |
| Schema hallucination | LLM invented `order_date` column that didn't exist | Tightened SQL rulebook in `schema_prompt.py` |
| KeyError on history | Inconsistent dictionary keys across memory turns | Synchronized all keys across the loop |
| MySQL Error 1064 | LLM returned plain English instead of SQL | Added `HISTORY_REQUEST` keyword routing to bypass DB |

---

## 📚 What I Learned

> Building from scratch means no framework hides the errors. Which means no framework hides the understanding.

- The difference between a **pipeline** and a true **autonomous agent** (it's the loop + memory + tool orchestration)
- How JSON tool schemas form the contract between an LLM and Python functions
- How sliding window memory keeps context within limits across multi-turn conversations
- How the sub-agent pattern works — an agent calling another agent internally
- How to migrate a terminal-based Python app into a production-ready web UI with Chainlit

---

## 📄 License

MIT License — feel free to use, fork, and build on this.

---

## 🙋 Author

**Jainil** — Computer Engineering Student  
[LinkedIn](https://www.linkedin.com/in/jainil-chavda/) • [GitHub](https://github.com/Jainil26/Ai-Database-Agent)

> ⭐ If this helped you understand how AI agents actually work under the hood, drop a star!
