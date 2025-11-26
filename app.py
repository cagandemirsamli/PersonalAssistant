import streamlit as st
import asyncio
from agent_modules.expense_agent import create_expense_agent
from agent_modules.academic_agent import create_academic_agent
from agents import Runner, SQLiteSession

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
st.markdown('<p class="sub-header">Expenses, Budgets, Assignments & Exams</p>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "expense_agent" not in st.session_state:
    st.session_state.expense_agent = create_expense_agent()

if "academic_agent" not in st.session_state:
    st.session_state.academic_agent = create_academic_agent()

if "session" not in st.session_state:
    st.session_state.session = SQLiteSession("PersonalAssistant")

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "current_agent" not in st.session_state:
    st.session_state.current_agent = "expense"


async def get_agent_response(user_input: str) -> str:
    """Run the current agent and get response."""
    if st.session_state.current_agent == "expense":
        agent = st.session_state.expense_agent.agent
    else:
        agent = st.session_state.academic_agent.agent
    
    result = await Runner.run(
        starting_agent=agent,
        input=user_input,
        session=st.session_state.session
    )
    return result.final_output


# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Select Agent")
    agent_choice = st.radio(
        "Choose assistant:",
        ["💰 Expense Tracker", "📚 Academic Tracker"],
        index=0 if st.session_state.current_agent == "expense" else 1,
        label_visibility="collapsed"
    )
    
    # Update current agent based on selection
    if "Expense" in agent_choice:
        st.session_state.current_agent = "expense"
    else:
        st.session_state.current_agent = "academic"
    
    st.divider()
    
    # Quick Actions based on current agent
    st.markdown("### ⚡ Quick Actions")
    
    if st.session_state.current_agent == "expense":
        if st.button("📊 Show all expenses", use_container_width=True):
            st.session_state.pending_prompt = "Show me all my expenses"
        
        if st.button("💳 Show all budgets", use_container_width=True):
            st.session_state.pending_prompt = "Show me all my budgets"
        
        st.divider()
        st.markdown("### 💡 Examples")
        st.markdown("""
        - *"Add 150 TL coffee expense"*
        - *"Create food budget of 3000 TL"*
        - *"How much spent on coffee?"*
        """)
    else:
        if st.button("📝 Show pending assignments", use_container_width=True):
            st.session_state.pending_prompt = "Show me all my pending assignments"
        
        if st.button("📅 Show upcoming exams", use_container_width=True):
            st.session_state.pending_prompt = "Show me all my upcoming exams"
        
        if st.button("✅ Show completed work", use_container_width=True):
            st.session_state.pending_prompt = "Show me all my completed assignments and exams"
        
        st.divider()
        st.markdown("### 💡 Examples")
        st.markdown("""
        - *"Add PS4 for COMP305 due Friday"*
        - *"Add Midterm 2 for CS101 on Dec 5"*
        - *"Mark PS3 from COMP305 as done"*
        - *"Enter grade 85 for CS101 Midterm"*
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
