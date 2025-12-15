import streamlit as st
import asyncio
from orchestrator import create_orchestrator
from agents import SQLiteSession

# Page config
st.set_page_config(
    page_title="Personal Assistant",
    page_icon="🤖",
    layout="centered"
)

# Custom styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .main-header {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4aa, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .sub-header {
        color: #8892b0;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🤖 Personal Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Expenses • Academics • Projects • Emails</p>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = create_orchestrator()

if "session" not in st.session_state:
    st.session_state.session = SQLiteSession("PersonalAssistant")

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


async def get_agent_response(user_input: str) -> str:
    """Process user input through the orchestrator."""
    return await st.session_state.orchestrator.process(
        user_input,
        st.session_state.session
    )


# Sidebar
with st.sidebar:
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("💰 Show all expenses", use_container_width=True):
        st.session_state.pending_prompt = "Show me all my expenses"
    
    if st.button("💳 Show all budgets", use_container_width=True):
        st.session_state.pending_prompt = "Show me all my budgets"
    
    if st.button("📝 Show pending assignments", use_container_width=True):
        st.session_state.pending_prompt = "Show me all my pending assignments"
    
    if st.button("📅 Show upcoming exams", use_container_width=True):
        st.session_state.pending_prompt = "Show me all my upcoming exams"
    
    if st.button("📧 Check important emails", use_container_width=True):
        st.session_state.pending_prompt = "Check my emails for important messages"
    
    if st.button("🚀 Show my projects", use_container_width=True):
        st.session_state.pending_prompt = "Show me all my projects"
    
    st.divider()
    
    st.markdown("### 💡 Example Queries")
    st.markdown("""
    **Expenses:**
    - *"Add 150 TL coffee expense"*
    - *"How much spent on food?"*
    
    **Academics:**
    - *"Add PS4 for COMP305 due Friday"*
    - *"What exams are coming up?"*
    
    **Projects:**
    - *"Show project Personal Assistant"*
    - *"Add milestone to project X"*
    
    **Emails:**
    - *"Check my unread emails"*
    - *"Any important emails?"*
    """)
    
    st.divider()
    
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🛑 Stop App", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.warning("App stopped. Close this browser tab and press Ctrl+C in terminal.")
        st.stop()


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle input from chat or pending prompt (from buttons)
prompt = st.chat_input("Ask me anything...")

# Check for pending prompt from sidebar buttons
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = asyncio.run(get_agent_response(prompt))
        st.markdown(response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})
