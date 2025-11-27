import json
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, SQLiteSession

# Load environment variables from .env file
load_dotenv()
# The agents library uses OPENAI_API_KEY from the environment automatically


class ProjectAgent():

    def __init__(self, name, instructions, model):
        self.name = name
        self.instructions = instructions
        self.model = model


        @function_tool
        def create_project(name: str, description: str):
            """
            Create a new project. Status defaults to "planning".
            Args:
                name: The name of the project (e.g., "Personal Assistant")
                description: A brief description of what the project is about
            Returns:
                Confirmation message that the project was created.
            """
            pass

        @function_tool
        def get_projects(status_filter: str = "all"):
            """
            List all projects, optionally filtered by status.
            Args:
                status_filter: Filter by status - "all", "in_progress", "completed", "paused", or "planning"
            Returns:
                A dict of projects matching the filter.
            """
            pass

        @function_tool
        def get_project_details(name: str):
            """
            Get full details about a project: description, status, technologies,
            milestones, features, notes, challenges, next steps, and links.
            Args:
                name: The name of the project
            Returns:
                Complete project information.
            """
            pass

        @function_tool
        def update_project_status(name: str, status: str):
            """
            Update the status of a project.
            Args:
                name: The name of the project
                status: New status - "planning", "in_progress", "paused", or "completed"
            Returns:
                Confirmation of the status change.
            """
            pass

        @function_tool
        def update_project_description(name: str, description: str):
            """
            Update the description of a project.
            Args:
                name: The name of the project
                description: The new description
            Returns:
                Confirmation that the description was updated.
            """
            pass

        @function_tool
        def remove_project(name: str):
            """
            Delete a project entirely.
            Args:
                name: The name of the project to remove
            Returns:
                Confirmation that the project was deleted.
            """
            pass


        @function_tool
        def add_milestone(name: str, milestone: str):
            """
            Add a new milestone to a project (status: pending).
            Args:
                name: The name of the project
                milestone: The milestone name (e.g., "Backend API")
            Returns:
                Confirmation that the milestone was added.
            """
            pass

        @function_tool
        def complete_milestone(name: str, milestone: str):
            """
            Mark a milestone as completed with today's date.
            Args:
                name: The name of the project
                milestone: The milestone to mark as completed
            Returns:
                Confirmation that the milestone was marked complete.
            """
            pass

        @function_tool
        def remove_milestone(name: str, milestone: str):
            """
            Remove a milestone from the project.
            Args:
                name: The name of the project
                milestone: The milestone to remove
            Returns:
                Confirmation that the milestone was removed.
            """
            pass


        @function_tool
        def add_technology(name: str, tech: str):
            """
            Add a technology to the project's tech stack.
            Args:
                name: The name of the project
                tech: The technology to add (e.g., "Python", "Docker")
            Returns:
                Confirmation that the technology was added.
            """
            pass

        @function_tool
        def remove_technology(name: str, tech: str):
            """
            Remove a technology from the project's tech stack.
            Args:
                name: The name of the project
                tech: The technology to remove
            Returns:
                Confirmation that the technology was removed.
            """
            pass


        @function_tool
        def add_feature(name: str, feature: str):
            """
            Add a feature to the project.
            Args:
                name: The name of the project
                feature: Description of the feature (e.g., "Real-time notifications")
            Returns:
                Confirmation that the feature was added.
            """
            pass

        @function_tool
        def remove_feature(name: str, feature: str):
            """
            Remove a feature from the project.
            Args:
                name: The name of the project
                feature: The feature to remove
            Returns:
                Confirmation that the feature was removed.
            """
            pass

        @function_tool
        def update_feature(name: str, old_feature: str, new_feature: str):
            """
            Update an existing feature's description.
            Args:
                name: The name of the project
                old_feature: The current feature text to find
                new_feature: The new feature text to replace it with
            Returns:
                Confirmation that the feature was updated.
            """
            pass


        @function_tool
        def add_note(name: str, content: str):
            """
            Add a progress note to the project (automatically dated with today).
            Args:
                name: The name of the project
                content: The note content (e.g., "Fixed async issue")
            Returns:
                Confirmation that the note was added.
            """
            pass

        @function_tool
        def remove_note(name: str, content: str):
            """
            Remove a note from the project by matching its content.
            Args:
                name: The name of the project
                content: The note content to remove
            Returns:
                Confirmation that the note was removed.
            """
            pass

        @function_tool
        def update_note(name: str, old_content: str, new_content: str):
            """
            Update an existing note's content (keeps the original date).
            Args:
                name: The name of the project
                old_content: The current note content to find
                new_content: The new content to replace it with
            Returns:
                Confirmation that the note was updated.
            """
            pass


        @function_tool
        def add_challenge(name: str, challenge: str):
            """
            Document a challenge faced in the project.
            Args:
                name: The name of the project
                challenge: Description of the challenge
            Returns:
                Confirmation that the challenge was documented.
            """
            pass

        @function_tool
        def remove_challenge(name: str, challenge: str):
            """
            Remove a challenge from the project.
            Args:
                name: The name of the project
                challenge: The challenge to remove
            Returns:
                Confirmation that the challenge was removed.
            """
            pass

        @function_tool
        def update_challenge(name: str, old_challenge: str, new_challenge: str):
            """
            Update an existing challenge's description.
            Args:
                name: The name of the project
                old_challenge: The current challenge text to find
                new_challenge: The new challenge text to replace it with
            Returns:
                Confirmation that the challenge was updated.
            """
            pass

        @function_tool
        def add_next_step(name: str, step: str):
            """
            Add a planned next step for the project.
            Args:
                name: The name of the project
                step: The next step (e.g., "Implement background scheduler")
            Returns:
                Confirmation that the next step was added.
            """
            pass

        @function_tool
        def remove_next_step(name: str, step: str):
            """
            Remove a next step from the project.
            Args:
                name: The name of the project
                step: The step to remove
            Returns:
                Confirmation that the next step was removed.
            """
            pass

        @function_tool
        def update_next_step(name: str, old_step: str, new_step: str):
            """
            Update an existing next step's description.
            Args:
                name: The name of the project
                old_step: The current step text to find
                new_step: The new step text to replace it with
            Returns:
                Confirmation that the next step was updated.
            """
            pass


        @function_tool
        def add_link(name: str, label: str, url: str):
            """
            Add a reference link to the project.
            Args:
                name: The name of the project
                label: Label for the link (e.g., "repo", "docs", "figma")
                url: The URL
            Returns:
                Confirmation that the link was added.
            """
            pass

        @function_tool
        def update_link(name: str, label: str, new_url: str):
            """
            Update an existing link's URL.
            Args:
                name: The name of the project
                label: The label of the link to update
                new_url: The new URL
            Returns:
                Confirmation that the link was updated.
            """
            pass

        @function_tool
        def remove_link(name: str, label: str):
            """
            Remove a link from the project.
            Args:
                name: The name of the project
                label: The label of the link to remove
            Returns:
                Confirmation that the link was removed.
            """
            pass


        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=[
                create_project, get_projects, get_project_details,
                update_project_status, update_project_description, remove_project,
                add_milestone, complete_milestone, remove_milestone,
                add_technology, remove_technology,
                add_feature, update_feature, remove_feature,
                add_note, update_note, remove_note,
                add_challenge, update_challenge, remove_challenge,
                add_next_step, update_next_step, remove_next_step,
                add_link, update_link, remove_link
            ],
            model=model
        )

    def load_projects(self, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            try:
                with open(full_path, 'r') as f:
                    projects = json.load(f)
            except json.JSONDecodeError:
                projects = {}
        else:
            projects = {}

        return projects

    def close_projects(self, projects, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            json.dump(projects, f, indent=4)


def get_instructions():
    """Generate instructions with current date."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"""
Personality: You are an AI agent that tracks personal projects and their progress.

Purpose: To store project information, track milestones, document progress notes,
and provide detailed summaries when asked about projects.

CURRENT DATE: {today}

Capabilities:
- Create and manage projects with descriptions and status
- Track milestones (pending/completed)
- Maintain tech stack for each project
- Record features, challenges, and next steps
- Add dated progress notes
- Store reference links

When asked about a project, provide a COMPREHENSIVE overview including:
1. Description and current status
2. Technologies being used
3. Milestones (completed ✅ and pending ⏳)
4. Features implemented
5. Current challenges
6. Planned next steps
7. Recent progress notes

Use CURRENT DATE to reference relative dates like "today", "yesterday", etc.
"""


def create_project_agent():
    """Factory function to create a ProjectAgent instance."""
    return ProjectAgent(
        name="ProjectAgent",
        instructions=get_instructions(),
        model="gpt-4.1-mini"
    )


if __name__ == "__main__":
    project_agent = create_project_agent()
    session = SQLiteSession("ProjectAgent Communication")

    async def main():
        print("Project Agent ready! Type 'quit' to exit.\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            result = await Runner.run(
                starting_agent=project_agent.agent,
                input=user_input,
                session=session
            )
            print(f"\nAgent: {result.final_output}\n")

    asyncio.run(main())