"""
Orchestrator Agent
Routes user requests to the appropriate specialized agent.
"""

import asyncio
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, SQLiteSession

# Import all specialized agents
from agent_modules.expense_agent import create_expense_agent
from agent_modules.academic_agent import create_academic_agent
from agent_modules.project_agent import create_project_agent
from agent_modules.email_agent.email_agent import create_email_agent

load_dotenv()


class Orchestrator:
    """
    Routes user requests to the appropriate specialized agent.
    
    The orchestrator acts as a smart dispatcher:
    1. Analyzes user intent
    2. Routes to the correct specialist agent
    3. Returns the specialist's response
    """
    
    def __init__(self):
        # Create all specialized agents (but don't initialize their services yet)
        print("Initializing specialized agents...")
        self.expense_agent = create_expense_agent()
        self.academic_agent = create_academic_agent()
        self.project_agent = create_project_agent()
        self.email_agent = create_email_agent()
        print("All agents initialized!")
        
        # Dictionary to map agent names to their agent objects
        self.agents = {
            "expense": self.expense_agent.agent,
            "academic": self.academic_agent.agent,
            "project": self.project_agent.agent,
            "email": self.email_agent.agent
        }
        
        # Now let's create the routing tools and orchestrator agent
        self._create_routing_tools()
        self._create_orchestrator_agent()
    
    def _create_routing_tools(self):
        """
        Create the routing tools that the orchestrator can call.
        Each tool routes to a different specialist agent.
        """
        
        # These will store the routing decision
        self.routing_decision = None
        self.request_to_forward = None
        
        @function_tool
        def route_to_expense(user_request: str):
            """
            Route to the Expense Agent for money-related queries.
            Use for: expenses, budgets, spending, costs, money tracking, payments.
            Examples: "add expense", "create budget", "how much spent", "TL", "dollars"
            """
            self.routing_decision = "expense"
            self.request_to_forward = user_request
            return f"Routing to Expense Agent: {user_request}"
        
        @function_tool
        def route_to_academic(user_request: str):
            """
            Route to the Academic Agent for school-related queries.
            Use for: assignments, homework, exams, deadlines, grades, courses, classes.
            Examples: "add assignment", "exam date", "deadline", "grade", "course"
            """
            self.routing_decision = "academic"
            self.request_to_forward = user_request
            return f"Routing to Academic Agent: {user_request}"
        
        @function_tool
        def route_to_project(user_request: str):
            """
            Route to the Project Agent for personal project tracking.
            Use for: projects, milestones, features, tech stack, development progress.
            Examples: "my projects", "add milestone", "project status", "features"
            """
            self.routing_decision = "project"
            self.request_to_forward = user_request
            return f"Routing to Project Agent: {user_request}"
        
        @function_tool
        def route_to_email(user_request: str):
            """
            Route to the Email Agent for Gmail-related queries.
            Use for: emails, inbox, unread messages, important emails, check mail.
            Examples: "check emails", "unread", "important emails", "inbox"
            """
            self.routing_decision = "email"
            self.request_to_forward = user_request
            return f"Routing to Email Agent: {user_request}"
        
        @function_tool
        def general_response(response: str):
            """
            Respond directly for general questions, greetings, or unclear requests.
            Use for: greetings, general questions, clarifications, asking what you can do.
            Examples: "hello", "what can you do", "help", unclear requests
            """
            self.routing_decision = "general"
            self.request_to_forward = response
            return response
        
        # Store tools so we can pass them to the orchestrator agent
        self.routing_tools = [
            route_to_expense,
            route_to_academic,
            route_to_project,
            route_to_email,
            general_response
        ]
    
    def _create_orchestrator_agent(self):
        """
        Create the orchestrator agent with routing tools and instructions.
        """
        
        today = datetime.now().strftime("%A, %B %d, %Y")
        
        instructions = f"""
You are an intelligent router for a Personal Assistant system.

CURRENT DATE: {today}

Your job is to understand the user's request and route it to the correct specialized agent:

1. **Expense Agent** - For anything about money:
   - Adding/viewing expenses
   - Creating/checking budgets
   - Spending analysis
   - Keywords: expense, budget, spent, cost, money, TL, dollars, payment, coffee, food

2. **Academic Agent** - For anything about school:
   - Assignments and homework
   - Exams and grades
   - Deadlines and due dates
   - Keywords: assignment, homework, exam, midterm, final, grade, course, class, due

3. **Project Agent** - For personal/side projects:
   - Project management
   - Milestones and features
   - Tech stack and progress notes
   - Keywords: project, milestone, feature, development, coding, tech stack

4. **Email Agent** - For Gmail-related requests:
   - Checking emails
   - Unread messages
   - Important emails
   - Keywords: email, inbox, unread, mail, gmail, important

5. **General Response** - For everything else:
   - Greetings ("hi", "hello")
   - Questions about what you can do
   - Unclear requests (ask for clarification)

IMPORTANT RULES:
- ALWAYS route to exactly ONE agent per request
- Forward the user's COMPLETE original request to the specialist
- If unsure which agent, ask the user to clarify
- For greetings, use general_response() with a friendly message

When routing, call the appropriate route_to_X() function and pass the user's original request.
"""
        
        self.orchestrator = Agent(
            name="Orchestrator",
            instructions=instructions,
            tools=self.routing_tools,
            model="gpt-4.1-mini"
        )
    
    async def process(self, user_input: str, session: SQLiteSession) -> str:
        """
        Process user input through the orchestrator.
        
        Flow:
        1. Orchestrator analyzes intent
        2. Routes to specialist agent
        3. Returns specialist's response
        """
        
        # Reset routing decision
        self.routing_decision = None
        self.request_to_forward = None
        
        # Step 1: Let orchestrator decide where to route
        route_result = await Runner.run(
            starting_agent=self.orchestrator,
            input=user_input,
            session=session
        )
        
        # Step 2: Check if a routing decision was made
        # (The routing tools set self.routing_decision when called)
        if self.routing_decision == "general":
            # General response - return the orchestrator's output directly
            return route_result.final_output
        
        elif self.routing_decision and self.routing_decision in self.agents:
            # Route to the appropriate specialist agent
            specialist_result = await Runner.run(
                starting_agent=self.agents[self.routing_decision],
                input=self.request_to_forward or user_input,
                session=session
            )
            return specialist_result.final_output
        
        else:
            # No routing decision made (orchestrator didn't call a routing tool)
            # Return orchestrator's response as fallback
            return route_result.final_output


def create_orchestrator():
    """Factory function to create an Orchestrator instance."""
    return Orchestrator()


# For standalone testing
if __name__ == "__main__":
    orchestrator = create_orchestrator()
    session = SQLiteSession("OrchestratorTest")
    
    async def main():
        print("="*60)
        print("ORCHESTRATOR TEST")
        print("="*60)
        print("\nThis orchestrator routes requests to specialized agents.")
        print("Try: 'Add 50 TL for coffee', 'Check my emails', 'Show my projects', etc.")
        print("Type 'quit' to exit.\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n" + "="*60)
            response = await orchestrator.process(user_input, session)
            print("="*60)
            print(f"\nAssistant: {response}\n")
    
    asyncio.run(main())

