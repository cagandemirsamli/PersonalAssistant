import streamlit as st
import asyncio
from agent_modules.expense_agent import create_expense_agent
from agents import Runner, SQLiteSession

# Page config
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
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
st.markdown('<p class="main-header">💰 Expense Tracker</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Track expenses, manage budgets, stay in control</p>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = create_expense_agent()

if "session" not in st.session_state:
    st.session_state.session = SQLiteSession("ExpenseAgent")

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


async def get_agent_response(user_input: str) -> str:
    """Run the agent and get response."""
    result = await Runner.run(
        starting_agent=st.session_state.agent.agent,
        input=user_input,
        session=st.session_state.session
    )
    return result.final_output


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Sidebar with quick actions
with st.sidebar:
    st.markdown("### Quick Actions")
    
    if st.button("📊 Show all expenses", use_container_width=True):
        st.session_state.pending_prompt = "Show me all my expenses"
    
    if st.button("💳 Show all budgets", use_container_width=True):
        st.session_state.pending_prompt = "Show me all my budgets"
    
    st.divider()
    
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.markdown("### Example Commands")
    st.markdown("""
    - *"Add 150 TL coffee expense for today"*
    - *"Create a food budget of 3000 TL"*
    - *"How much have I spent on coffee?"*
    - *"Delete my transport budget"*
    """)

# Handle input from chat or pending prompt (from buttons)
prompt = st.chat_input("Ask about expenses or budgets...")

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
