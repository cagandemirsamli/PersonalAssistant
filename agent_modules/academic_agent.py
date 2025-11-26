import json
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, SQLiteSession

# Load environment variables from .env file
load_dotenv()
# The agents library uses OPENAI_API_KEY from the environment automatically

class AcademicAgent():

    def __init__(self, name, instructions, model):
        self.name = name
        self.instructions = instructions
        self.model = model

        @function_tool
        def set_assignment(heading: str, course: str, deadline: str):
            """
            Sets a new deadline regarding an assignment.
            Args:
                heading: The title of the assignment (e.g., "Homework 3")
                course: The course name (e.g., "CS101")
                deadline: The due date (e.g., "2025-12-01")
            Returns:
                A completion message that the deadline is correctly added.
            """
            assignments = self.load_assignments("data/assignments.json")
            assignments[heading] = {
                "course": course,
                "deadline": deadline,
                "completed": False
            }
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{heading}' for {course} (due {deadline}) added successfully!"


        @function_tool
        def get_assignments(show_completed: bool = False):
            """
            Retrieve assignments.
            Args:
                show_completed: If True, show completed assignments. If False, show only pending ones.
            Returns:
                A dict of assignments matching the filter.
            """
            assignments = self.load_assignments("data/assignments.json")
            if not assignments:
                return "No assignments found."
            
            filtered = {
                heading: data for heading, data in assignments.items()
                if data.get("completed", False) == show_completed
            }
            
            if not filtered:
                status = "completed" if show_completed else "pending"
                return f"No {status} assignments found."
            return filtered


        @function_tool
        def remove_assignment(heading: str):
            """
            Removes an assignment (use for cancelled assignments only).
            Args:
                heading: The title of the assignment to remove
            Returns:
                A success message stating that the assignment is successfully deleted.
            """
            assignments = self.load_assignments("data/assignments.json")
            if not assignments:
                return "No assignments found."
            
            if heading not in assignments:
                return f"No assignment found with heading '{heading}'."
            
            del assignments[heading]
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{heading}' removed successfully."


        @function_tool
        def update_assignment(heading: str, new_deadline: str):
            """
            Updates the deadline of an assignment.
            Args:
                heading: The title of the assignment to update
                new_deadline: The new due date
            Returns:
                A success message stating that the assignment info is successfully updated.
            """
            assignments = self.load_assignments("data/assignments.json")
            if not assignments:
                return "No assignments found."
            
            if heading not in assignments:
                return f"No assignment found with heading '{heading}'."
            
            prev_deadline = assignments[heading]["deadline"]
            assignments[heading]["deadline"] = new_deadline
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{heading}' deadline updated: {prev_deadline} → {new_deadline}"

        @function_tool
        def complete_assignment(heading: str):
            """
            Marks an assignment as completed.
            Args:
                heading: The title of the assignment to mark as done
            Returns:
                A success message confirming completion.
            """
            assignments = self.load_assignments("data/assignments.json")
            if not assignments:
                return "No assignments found."
            
            if heading not in assignments:
                return f"No assignment found with heading '{heading}'."
            
            if assignments[heading].get("completed", False):
                return f"Assignment '{heading}' is already marked as completed."
            
            assignments[heading]["completed"] = True
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{heading}' marked as completed!"

        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=[set_assignment, get_assignments, remove_assignment,
                   update_assignment, complete_assignment],
            model=model
        )




    def load_assignments(self, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            try:
                with open(full_path, 'r') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, list):
                        assignment_deadlines = {}
                        for idx, item in enumerate(loaded_data):
                            unique_key = f"{item.get('course', 'unknown')}_{item.get('heading', 'unknown')}_{idx}_{item.get('date', 'unknown')}_{idx}"
                            assignment_deadlines[unique_key] = item
                    else:
                        assignment_deadlines = loaded_data
            except json.JSONDecodeError:
                # File exists but has invalid JSON, start fresh
                assignment_deadlines = {}
        else:
            assignment_deadlines = {}

        return assignment_deadlines


    def close_assignments(self, assignments, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            json.dump(assignments, f, indent=4)


def get_instructions():
    """Generate instructions with current date."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"""
Personality: You are an AI agent that keeps track of user assignments and exams in college.

Purpose: To record assignment deadlines and exam dates, keep track of completed/incompleted assignments,
and complete other related tasks regarding user demand.

CURRENT DATE: {today}

Capabilities:
- Record and retrieve assignments (heading, course, deadline)
- Create, update, and remove assignments per heading
- Track assignment due dates
- Alert when deadline of an assignment becomes too close

Important Rules:
1. If the deadline of an assignment isn't entered, ask for the user once more to enter it.
2. Alert the user when an assignment's deadline reaches within 2 days.
3. Always inform about how many days the user has to complete a given assignment.
4. Use the CURRENT DATE above to calculate time remaining accurately. Also use CURRENT DATE to calculate the dates corresponding to terms like tomorrow, yesterday, 3 days ago, etc.
"""

def create_academic_agent():
    """Factory function to create an AcademicAgent instance."""
    return AcademicAgent(
        name="AcademicAgent",
        instructions=get_instructions(),
        model="gpt-4.1-mini"
    )


if __name__ == "__main__":
    academic_agent = create_academic_agent()
    session = SQLiteSession("AcademicAgent Communication")

    async def main():
        print("Academic Agent ready! Type 'quit' to exit.\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            result = await Runner.run(
                starting_agent=academic_agent.agent,
                input=user_input,
                session=session
            )
            print(f"\nAgent: {result.final_output}\n")

    asyncio.run(main())