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


        # Assignment helper functions
        @function_tool
        def set_assignment(course: str, context: str, deadline: str):
            """
            Sets a new assignment for a course.
            Args:
                course: The course name (e.g., "CS101")
                context: The assignment name - PS3, Homework 1, Project, etc.
                deadline: The due date (e.g., "2025-12-01")
            Returns:
                A completion message that the assignment is correctly added.
            """
            course_key = course.upper()
            context_key = context.upper()
            assignments = self.load_assignments("data/assignments.json")
            if course_key not in assignments:
                assignments[course_key] = {}
            assignments[course_key][context_key] = {
                "deadline": deadline,
                "completed": False
            }
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{context}' for {course} (due {deadline}) added successfully!"


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
            
            # Filter assignments - structure is: {course: {context: {deadline, completed}}}
            filtered = {}
            for course_key, contexts in assignments.items():
                matching_contexts = {
                    ctx: data for ctx, data in contexts.items()
                    if data.get("completed", False) == show_completed
                }
                if matching_contexts:
                    filtered[course_key] = matching_contexts
            
            if not filtered:
                status = "completed" if show_completed else "pending"
                return f"No {status} assignments found."
            return filtered


        @function_tool
        def remove_assignment(course: str, context: str):
            """
            Removes an assignment (use for cancelled assignments only).
            Args:
                course: The course name
                context: The assignment name (PS3, Homework 1, etc.)
            Returns:
                A success message stating that the assignment is successfully deleted.
            """
            course_key = course.upper()
            context_key = context.upper()
            assignments = self.load_assignments("data/assignments.json")
            if not assignments:
                return "No assignments found."
            
            if course_key not in assignments:
                return f"No assignments found for course '{course}'."
            
            if context_key not in assignments[course_key]:
                return f"Assignment '{context}' not found in course '{course}'."
            
            del assignments[course_key][context_key]
            # Clean up empty course entry
            if not assignments[course_key]:
                del assignments[course_key]
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{context}' from course '{course}' removed successfully."


        @function_tool
        def update_assignment(course: str, context: str, new_deadline: str):
            """
            Updates the deadline of an assignment.
            Args:
                course: The course name
                context: The assignment name (PS3, Homework 1, etc.)
                new_deadline: The new due date
            Returns:
                A success message stating that the assignment info is successfully updated.
            """
            course_key = course.upper()
            context_key = context.upper()
            assignments = self.load_assignments("data/assignments.json")
            if not assignments:
                return "No assignments found."
            
            if course_key not in assignments:
                return f"No assignments found for course '{course}'."
            
            if context_key not in assignments[course_key]:
                return f"Assignment '{context}' not found in course '{course}'."
            
            prev_deadline = assignments[course_key][context_key]["deadline"]
            assignments[course_key][context_key]["deadline"] = new_deadline
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{context}' from '{course}' deadline updated: {prev_deadline} → {new_deadline}"

        @function_tool
        def complete_assignment(course: str, context: str):
            """
            Marks an assignment as completed.
            Args:
                course: The course name
                context: The assignment name (PS3, Homework 1, etc.)
            Returns:
                A success message confirming completion.
            """
            course_key = course.upper()
            context_key = context.upper()
            assignments = self.load_assignments("data/assignments.json")
            if not assignments:
                return "No assignments found."
            
            if course_key not in assignments:
                return f"No assignments found for course '{course}'."
            
            if context_key not in assignments[course_key]:
                return f"Assignment '{context}' not found in course '{course}'."
            
            if assignments[course_key][context_key].get("completed", False):
                return f"Assignment '{context}' from course '{course}' is already marked as completed."
            
            assignments[course_key][context_key]["completed"] = True
            self.close_assignments(assignments, "data/assignments.json")
            return f"Assignment '{context}' from course '{course}' marked as completed!"



        # Exam helper functions
        @function_tool
        def set_exam(course: str, context: str, date: str):
            """
            Sets a new exam for a course.
            Args:
                course: The course name (e.g., "CS101")
                context: The exam type - Midterm 1, Midterm 2, Final, etc.
                date: The date of the exam (e.g., "2025-12-01")
            Returns:
                A completion message that the exam is correctly added.
            """
            course_key = course.upper()
            context_key = context.upper()
            exams = self.load_exams("data/exams.json")
            if course_key not in exams:
                exams[course_key] = {}
            exams[course_key][context_key] = {
                "date": date,
                "completed": False,
                "grade": None
            }
            self.close_exams(exams, "data/exams.json")
            return f"Exam '{context}' for {course} (on {date}) added successfully!"

        @function_tool
        def get_exams(show_completed: bool = False):
            """
            Retrieve exams.
            Args:
                show_completed: If True, show completed exams. If False, show only pending ones.
            Returns:
                A dict of exams matching the filter.
            """
            exams = self.load_exams("data/exams.json")
            if not exams:
                return "No exams found."

            # Filter exams - structure is: {course: {context: {date, completed}}}
            filtered = {}
            for course_key, contexts in exams.items():
                matching_contexts = {
                    ctx: data for ctx, data in contexts.items()
                    if data.get("completed", False) == show_completed
                }
                if matching_contexts:
                    filtered[course_key] = matching_contexts

            if not filtered:
                status = "completed" if show_completed else "pending"
                return f"No {status} exams found."
            return filtered

        @function_tool
        def remove_exam(course: str, context: str):
            """
            Removes an exam (use for cancelled exams only).
            Args:
                course: The course name
                context: The exam type (Midterm 1, Final, etc.)
            Returns:
                A success message stating that the exam is successfully deleted.
            """
            course_key = course.upper()
            context_key = context.upper()
            exams = self.load_exams("data/exams.json")
            if not exams:
                return "No exams found."

            if course_key not in exams:
                return f"No exams found for course '{course}'."

            if context_key not in exams[course_key]:
                return f"Exam '{context}' not found in course '{course}'."

            del exams[course_key][context_key]
            # Clean up empty course entry
            if not exams[course_key]:
                del exams[course_key]
            self.close_exams(exams, "data/exams.json")
            return f"Exam '{context}' from course '{course}' removed successfully."

        @function_tool
        def update_exam(course: str, context: str, new_date: str):
            """
            Updates the date of an exam.
            Args:
                course: The course name
                context: The exam type (Midterm 1, Final, etc.)
                new_date: The new date of the exam
            Returns:
                A success message stating that the exam info is successfully updated.
            """
            course_key = course.upper()
            context_key = context.upper()
            exams = self.load_exams("data/exams.json")
            if not exams:
                return "No exams found."

            if course_key not in exams:
                return f"No exams found for course '{course}'."

            if context_key not in exams[course_key]:
                return f"Exam '{context}' not found in course '{course}'."

            prev_date = exams[course_key][context_key]["date"]
            exams[course_key][context_key]["date"] = new_date
            self.close_exams(exams, "data/exams.json")
            return f"Exam '{context}' from '{course}' date updated: {prev_date} → {new_date}"

        @function_tool
        def complete_exam(course: str, context: str):
            """
            Marks an exam as completed (taken).
            Args:
                course: The course name
                context: The exam type (Midterm 1, Final, etc.)
            Returns:
                A success message confirming completion.
            """
            course_key = course.upper()
            context_key = context.upper()
            exams = self.load_exams("data/exams.json")
            if not exams:
                return "No exams found."

            if course_key not in exams:
                return f"No exams found for course '{course}'."

            if context_key not in exams[course_key]:
                return f"Exam '{context}' not found in course '{course}'."

            if exams[course_key][context_key].get("completed", False):
                return f"Exam '{context}' from course '{course}' is already marked as completed."

            exams[course_key][context_key]["completed"] = True
            self.close_exams(exams, "data/exams.json")
            return f"Exam '{context}' from course '{course}' marked as completed!"


        @function_tool
        def enter_exam_score(course: str, context: str, grade: int):
            """
            Enters an exam grade/score.
            Args:
                course: The course name
                context: The exam type (Midterm 1, Final, etc.)
                grade: The grade/score to be entered
            Returns:
                A success message confirming grade entry.
            """
            course_key = course.upper()
            context_key = context.upper()
            exams = self.load_exams("data/exams.json")
            if not exams:
                return "No exams found."

            if course_key not in exams:
                return f"No exams found for course '{course}'."

            if context_key not in exams[course_key]:
                return f"Exam '{context}' not found in course '{course}'."

            if exams[course_key][context_key].get("grade") is not None:
                return f"A grade for exam '{context}' from course '{course}' is already entered. Current grade: {exams[course_key][context_key]['grade']}"

            exams[course_key][context_key]["grade"] = grade
            self.close_exams(exams, "data/exams.json")
            return f"Grade '{grade}' successfully added for exam '{context}' of '{course}'."

        # Register all tools with the agent
        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=[set_assignment, get_assignments, remove_assignment,
                   update_assignment, complete_assignment,
                   set_exam, get_exams, remove_exam,
                   update_exam, complete_exam, enter_exam_score],
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
                        assignments = {}
                        for idx, item in enumerate(loaded_data):
                            unique_key = f"{item.get('heading', 'unknown')}_{item.get('course', 'unknown')}_{idx}_{item.get('deadline', 'unknown')}_{idx}"
                            assignments[unique_key] = item
                    else:
                        assignments = loaded_data
            except json.JSONDecodeError:
                # File exists but has invalid JSON, start fresh
                assignments = {}
        else:
            assignments = {}

        return assignments


    def close_assignments(self, assignments, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            json.dump(assignments, f, indent=4)

    def load_exams(self, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            try:
                with open(full_path, 'r') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, list):
                        exams = {}
                        for idx, item in enumerate(loaded_data):
                            unique_key = f"{item.get('course', 'unknown')}_{item.get('context', 'unknown')}_{idx}_{item.get('date', 'unknown')}_{idx}"
                            exams[unique_key] = item
                    else:
                        exams = loaded_data
            except json.JSONDecodeError:
                # File exists but has invalid JSON, start fresh
                exams = {}
        else:
            exams = {}

        return exams


    def close_exams(self, exams, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            json.dump(exams, f, indent=4)


def get_instructions():
    """Generate instructions with current date."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"""
Personality: You are an AI agent that keeps track of user assignments and exams in college.

Purpose: To record assignment deadlines and exam dates, keep track of completed/incompleted work,
and complete other related tasks regarding user demand.

CURRENT DATE: {today}

Capabilities:
ASSIGNMENTS:
- Record and retrieve assignments (heading, course, deadline)
- Create, update, and remove assignments per heading
- Track assignment due dates and completion status

EXAMS:
- Record and retrieve exams (course, context like Midterm/Final, date)
- Track exam dates and completion status
- Record exam grades/scores

Important Rules:
1. If a deadline/date isn't entered, ask the user to provide it.
2. Alert the user when a deadline reaches within 2 days.
3. Always inform about how many days until an assignment or exam.
4. Use the CURRENT DATE above to calculate time remaining accurately. Also use CURRENT DATE to calculate dates for terms like tomorrow, yesterday, 3 days ago, etc.
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