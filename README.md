# 🤖 Personal Assistant

A multi-agent AI system that helps you manage expenses, academics, projects, and emails through natural language conversation.

## 🎯 Overview

This Personal Assistant uses multiple specialized AI agents that work together through an intelligent orchestrator. Instead of manually switching between different tools, you simply talk to it naturally, and it automatically routes your requests to the right specialist.

**Example:**
- You say: "Add 50 TL for coffee"
- Orchestrator analyzes: "This is about expenses"
- Routes to: Expense Agent
- Response: "Expense of 50 TL for coffee added!"

---

## 🏗️ Architecture

### The Orchestrator Pattern

```
┌─────────────────────────────────────────────────┐
│                   USER                           │
└────────────────────┬────────────────────────────┘
                     │
                     │ "Add 50 TL for coffee"
                     ↓
┌─────────────────────────────────────────────────┐
│            ORCHESTRATOR AGENT                   │
│  • Analyzes user intent                          │
│  • Routes to appropriate specialist              │
│  • Doesn't know HOW to do tasks                  │
└────────────────────┬────────────────────────────┘
                     │
        Routes to ───┼───→ Specialist Agents
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│           SPECIALIST AGENTS                     │
│                                                  │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │  Expense   │  │  Academic  │  │  Project │ │
│  │   Agent    │  │   Agent    │  │  Agent   │ │
│  └────────────┘  └────────────┘  └──────────┘ │
│                                                  │
│  ┌────────────┐                                 │
│  │   Email    │                                 │
│  │   Agent    │                                 │
│  └────────────┘                                 │
│                                                  │
│  Each has specific tools and domain knowledge   │
└─────────────────────────────────────────────────┘
```

**Key Concept:** The orchestrator is a "smart router" that understands intent but doesn't execute tasks. Specialist agents know HOW to do their specific tasks.

---

## ✨ Features

### 💰 Expense Agent
- Track expenses by category (coffee, food, transport, etc.)
- Create and manage budgets
- Monitor spending vs. budget limits
- Automatic budget warnings
- All amounts in Turkish Lira (TL)

### 📚 Academic Agent
- Manage assignments with deadlines
- Track exam dates and grades
- Mark assignments/exams as completed
- View pending vs. completed work
- Calculate days until deadlines

### 🚀 Project Agent
- Track personal/side projects
- Manage milestones (pending/completed)
- Document features, challenges, and next steps
- Maintain tech stack per project
- Add progress notes with dates
- Store reference links

### 📧 Email Agent
- Connect to Gmail accounts (multiple accounts supported)
- Check unread emails
- Search emails by keyword, sender, or date
- Identify important emails (assignments, deadlines, exams, urgent)
- Read full email content

---

## 🚀 Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- (Optional) Google Cloud Project with Gmail API enabled (for Email Agent)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd PersonalAssistant
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Gmail API Setup (Optional, for Email Agent):**
   
   If you want to use the Email Agent:
   
   a. Go to [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a project (or use existing)
   
   c. Enable Gmail API:
      - Navigate to "APIs & Services" → "Library"
      - Search for "Gmail API"
      - Click "Enable"
   
   d. Create OAuth credentials:
      - Go to "APIs & Services" → "Credentials"
      - Click "Create Credentials" → "OAuth client ID"
      - Application type: "Desktop app"
      - Download `client_secret.json`
   
   e. Configure OAuth consent screen:
      - Go to "OAuth consent screen"
      - Choose "External" user type
      - Add test users (your Gmail accounts)
   
   f. Place credentials:
      ```
      data/email_credentials/client_secret.json
      ```

---

## 💻 Usage

### Running the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Example Queries

**Expenses:**
- "Add 150 TL for coffee"
- "Show me all my expenses"
- "Create a food budget of 3000 TL"
- "How much did I spend on coffee this month?"

**Academics:**
- "Add PS4 for COMP305 due Friday"
- "What assignments are due soon?"
- "Mark PS3 from COMP305 as done"
- "Enter grade 85 for CS101 Midterm"

**Projects:**
- "Create a project called Personal Assistant"
- "Show me my projects"
- "Add milestone 'Backend API' to project X"
- "What are the next steps for project Y?"

**Emails:**
- "Check my emails"
- "Show unread emails"
- "Check for important emails"
- "Connect my personal Gmail account"

---

## 📁 Project Structure

```
PersonalAssistant/
├── agent_modules/
│   ├── __init__.py
│   ├── expense_agent.py          # Expense & budget management
│   ├── academic_agent.py          # Assignments & exams
│   ├── project_agent.py           # Project tracking
│   └── email_agent/
│       ├── __init__.py
│       ├── email_agent.py         # Main email agent
│       └── gmail_auth.py          # Gmail OAuth authentication
├── data/
│   ├── email_credentials/
│   │   ├── client_secret.json     # Gmail API credentials
│   │   └── *_token.pickle         # OAuth tokens (per account)
│   ├── expense_file.json          # Expense data
│   ├── budget_file.json           # Budget data
│   ├── assignments.json           # Academic assignments
│   ├── exams.json                 # Exam data
│   └── projects.json              # Project data
├── orchestrator.py                # Routes requests to agents
├── app.py                         # Streamlit UI
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## 🔧 How It Works

### 1. User Input Flow

```
User types: "Add 50 TL for coffee"
        ↓
app.py receives input
        ↓
orchestrator.process(user_input)
        ↓
Orchestrator Agent analyzes intent:
  - Sees "50 TL", "coffee" → expense-related
  - Calls route_to_expense()
        ↓
Routes to Expense Agent
        ↓
Expense Agent executes:
  - Calls create_expense("coffee", 50)
  - Saves to expense_file.json
  - Returns confirmation
        ↓
Response flows back to user
```

### 2. Authentication (Email Agent)

The Email Agent uses OAuth2 to access Gmail:

**First Time:**
1. User: "Connect my personal Gmail"
2. Browser opens → Google login
3. User grants permission
4. Token saved to `personal_token.pickle`
5. Gmail service ready

**Subsequent Times:**
1. Load saved token
2. If expired → refresh automatically
3. If refresh fails → re-authenticate (opens browser)
4. Use Gmail service

### 3. Data Storage

All data is stored as JSON files in `data/`:
- Simple, human-readable format
- Easy to backup/restore
- No database setup required

**Data Structure Examples:**

**Expenses:**
```json
{
  "COFFEE": [
    {"date": "2024-12-15", "amount": 50},
    {"date": "2024-12-14", "amount": 30}
  ]
}
```

**Projects:**
```json
{
  "PERSONAL_ASSISTANT": {
    "name": "Personal Assistant",
    "status": "in_progress",
    "milestones": [
      {"name": "Backend API", "status": "completed", "completed_date": "2024-12-10"}
    ]
  }
}
```

---

## 🎓 Agents Explained

### Orchestrator Agent

**Role:** Smart router/dispatcher

**What it knows:**
- Which agent handles what type of request
- How to identify user intent
- When to route vs. respond directly

**What it doesn't know:**
- How to add an expense (Expense Agent knows)
- How to check emails (Email Agent knows)
- Domain-specific details

**Tools:**
- `route_to_expense(request)` - Routes to Expense Agent
- `route_to_academic(request)` - Routes to Academic Agent
- `route_to_project(request)` - Routes to Project Agent
- `route_to_email(request)` - Routes to Email Agent
- `general_response(message)` - Handles greetings/general queries

---

### Expense Agent

**Role:** Money management

**Capabilities:**
- Add/view expenses by category
- Create/edit budgets
- Track spending vs. limits
- Calculate totals per category

**Data Files:**
- `data/expense_file.json` - All expenses
- `data/budget_file.json` - Budget limits and spending

**Key Functions:**
- `add_expense(category, amount, date)` - Record expense
- `get_expenses(category)` - View expenses
- `set_budget(category, amount)` - Create budget
- `get_category_total(category)` - Calculate spending

---

### Academic Agent

**Role:** School/academic tracking

**Capabilities:**
- Manage assignments (create, update, complete)
- Track exams (dates, grades)
- Filter by completion status
- Calculate days until deadlines

**Data Files:**
- `data/assignments.json` - All assignments
- `data/exams.json` - All exams

**Key Functions:**
- `set_assignment(course, context, deadline)` - Add assignment
- `get_assignments(show_completed)` - List assignments
- `complete_assignment(course, context)` - Mark done
- `set_exam(course, context, date)` - Add exam

---

### Project Agent

**Role:** Personal project management

**Capabilities:**
- Create/manage projects
- Track milestones (pending/completed)
- Document features, challenges, next steps
- Add progress notes
- Store tech stack and links

**Data Files:**
- `data/projects.json` - All project data

**Key Functions:**
- `create_project(name, description)` - New project
- `add_milestone(name, milestone_name)` - Track progress
- `add_feature(name, feature)` - Document features
- `add_note(name, content)` - Progress notes

---

### Email Agent

**Role:** Gmail integration

**Capabilities:**
- Connect to multiple Gmail accounts
- Check unread emails
- Search emails
- Identify important emails (keywords: assignment, deadline, exam, etc.)

**Authentication:**
- Uses OAuth2 via Google API
- Tokens stored per account
- Auto-refresh on expiry

**Key Functions:**
- `connect_account(account_name)` - Authenticate Gmail
- `get_unread_emails(account)` - List unread
- `check_important_emails(account)` - Find important
- `search_emails(account, query)` - Search Gmail

**Files:**
- `agent_modules/email_agent/gmail_auth.py` - OAuth handling
- `data/email_credentials/client_secret.json` - API credentials
- `data/email_credentials/*_token.pickle` - User tokens

---

## 🛠️ Technical Details

### Technology Stack

- **Python 3.8+**
- **Streamlit** - Web UI
- **OpenAI Agents SDK** - LLM agent framework
- **Google Gmail API** - Email access
- **JSON** - Data storage

### Key Libraries

```
openai
openai-agents
streamlit
python-dotenv
google-auth
google-auth-oauthlib
google-api-python-client
```

### Agent Framework

Uses the `@function_tool` decorator pattern:
- LLM sees available tools as function signatures
- Decides which tool to call
- Tool executes and returns result
- LLM formats response to user

**Example Tool:**
```python
@function_tool
def add_expense(category: str, amount: float, date: str = None):
    """
    Add a new expense.
    Args:
        category: The category (e.g., "coffee")
        amount: Amount in TL
        date: Optional date (defaults to today)
    """
    # Implementation...
    return "Expense added!"
```

---

## 🎯 Key Concepts Learned

### 1. Multi-Agent Architecture
- Specialized agents for specific domains
- Orchestrator for routing
- Separation of concerns

### 2. OAuth2 Authentication
- How to authenticate with Google APIs
- Token management (save, load, refresh)
- Browser-based authentication flow

### 3. Function Calling / Tool Use
- LLMs can call functions
- Tools extend LLM capabilities
- Structured data in/out

### 4. Agent Orchestration
- How to route requests intelligently
- When to use orchestrator vs. direct agent access
- Handling routing failures gracefully

---

## 📝 Notes

- All monetary values are in Turkish Lira (TL)
- Dates use YYYY-MM-DD format
- Email Agent requires Gmail API setup
- Project keys are uppercase with underscores (e.g., `PERSONAL_ASSISTANT`)
- Tokens are stored as pickle files (binary format)

---

## 🔒 Security

- `.env` file contains API keys (DO NOT commit)
- `client_secret.json` contains OAuth credentials (DO NOT commit)
- Token files contain user authentication (DO NOT commit)
- All sensitive files are in `.gitignore`

---

## 🚧 Future Enhancements

Potential improvements:
- Background email monitoring with alerts
- Calendar integration
- Budget spending analysis/charts
- Project progress visualization
- Multi-language support

---

## 📄 License

This is a personal project for learning purposes.

---

## 🙏 Acknowledgments

Built using:
- OpenAI GPT models
- Streamlit
- Google Gmail API
- Python ecosystem

---

**Enjoy your Personal Assistant! 🎉**


