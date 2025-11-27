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

            name_key = name.upper().replace(" ", "_")

            projects = self.load_projects("data/projects.json")
            if name_key in projects:
                return f"Project '{name}' already exists."
            projects[name_key] = {
                "description": description,
                "status": "planning",
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "features": [],
                "milestones": [],
                "notes": [],
                "challenges": [],
                "technologies": [],
                "links": {},
                "next_steps": [],
            }
            self.close_projects(projects, "data/projects.json")
            return f"Project '{name_key}' added successfully!"


        @function_tool
        def get_projects(status_filter: str = "all"):
            """
            List all projects, optionally filtered by status.
            Args:
                status_filter: Filter by status - "all", "in_progress", "completed", "paused", or "planning"
            Returns:
                A dict of projects matching the filter.
            """

            projects = self.load_projects("data/projects.json")
            if not projects:
                return "No projects found."
            
            if status_filter == "all":
                return projects
            
            # Filter by status
            filtered = {
                name: data for name, data in projects.items()
                if data.get("status") == status_filter
            }
            
            if not filtered:
                return f"No projects with status '{status_filter}' found."
            return filtered

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            return projects[name_key]

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["status"] = status
            self.close_projects(projects, "data/projects.json")
            return f"Status of '{name_key}' successfully changed to '{status}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["description"] = description
            self.close_projects(projects, "data/projects.json")
            return f"Description of '{name_key}' successfully changed to '{description}'."

        @function_tool
        def remove_project(name: str):
            """
            Delete a project entirely.
            Args:
                name: The name of the project to remove
            Returns:
                Confirmation that the project was deleted.
            """
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects.pop(name_key)
            self.close_projects(projects, "data/projects.json")
            return f"'{name_key}' successfully removed from projects."


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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["features"].append(feature)
            self.close_projects(projects, "data/projects.json")
            return f"Feature '{feature}' added to '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if feature not in projects[name_key]["features"]:
                return f"Feature '{feature}' not found in project '{name}'."
            
            projects[name_key]["features"].remove(feature)
            self.close_projects(projects, "data/projects.json")
            return f"Feature '{feature}' removed from '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if old_feature not in projects[name_key]["features"]:
                return f"Feature '{old_feature}' not found in project '{name}'."
            
            idx = projects[name_key]["features"].index(old_feature)
            projects[name_key]["features"][idx] = new_feature
            self.close_projects(projects, "data/projects.json")
            return f"Feature updated: '{old_feature}' → '{new_feature}'."




        @function_tool
        def add_milestone(name: str, milestone_name: str, status: str = "pending", completed_date: str = None):
            """
            Add a new milestone to a project.
            Args:
                name: The name of the project
                milestone_name: The milestone name (e.g., "Backend API")
                status: The status - "pending" or "completed" (defaults to "pending")
                completed_date: The completion date if completed (format: YYYY-MM-DD), or null if pending
            Returns:
                Confirmation that the milestone was added.
            """
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["milestones"].append({
                "name": milestone_name,
                "status": status,
                "completed_date": completed_date
            })
            self.close_projects(projects, "data/projects.json")
            return f"Milestone '{milestone_name}' added to '{name_key}'."

        @function_tool
        def complete_milestone(name: str, milestone_name: str, completed_date: str = None):
            """
            Mark a milestone as completed.
            Args:
                name: The name of the project
                milestone_name: The milestone to mark as completed
                completed_date: Optional completion date (format: YYYY-MM-DD). Defaults to today.
            Returns:
                Confirmation that the milestone was marked complete.
            """
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            for m in projects[name_key]["milestones"]:
                if m["name"].lower() == milestone_name.lower():
                    m["status"] = "completed"
                    m["completed_date"] = completed_date or datetime.now().strftime("%Y-%m-%d")
                    self.close_projects(projects, "data/projects.json")
                    return f"Milestone '{milestone_name}' marked as completed."
            
            return f"Milestone '{milestone_name}' not found in project '{name}'."


        @function_tool
        def remove_milestone(name: str, milestone_name: str):
            """
            Remove a milestone from the project.
            Args:
                name: The name of the project
                milestone_name: The name of the milestone to remove
            Returns:
                Confirmation that the milestone was removed.
            """
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            original_count = len(projects[name_key]["milestones"])
            projects[name_key]["milestones"] = [
                m for m in projects[name_key]["milestones"]
                if m["name"].lower() != milestone_name.lower()
            ]
            
            if len(projects[name_key]["milestones"]) == original_count:
                return f"Milestone '{milestone_name}' not found in project '{name}'."
            
            self.close_projects(projects, "data/projects.json")
            return f"Milestone '{milestone_name}' removed from '{name_key}'."




        @function_tool
        def add_note(name: str, content: str, date: str = None):
            """
            Add a progress note to the project.
            Args:
                name: The name of the project
                content: The note content (e.g., "Fixed async issue")
                date: Optional date (format: YYYY-MM-DD). Defaults to today.
            Returns:
                Confirmation that the note was added.
            """
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["notes"].append({
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "content": content
            })
            self.close_projects(projects, "data/projects.json")
            return f"Note added to '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            original_count = len(projects[name_key]["notes"])
            projects[name_key]["notes"] = [
                n for n in projects[name_key]["notes"]
                if n["content"].lower() != content.lower()
            ]
            
            if len(projects[name_key]["notes"]) == original_count:
                return f"Note not found in project '{name}'."
            
            self.close_projects(projects, "data/projects.json")
            return f"Note removed from '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            for n in projects[name_key]["notes"]:
                if n["content"].lower() == old_content.lower():
                    n["content"] = new_content
                    self.close_projects(projects, "data/projects.json")
                    return f"Note updated in '{name_key}'."
            
            return f"Note not found in project '{name}'."




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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["challenges"].append(challenge)
            self.close_projects(projects, "data/projects.json")
            return f"Challenge added to '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if challenge not in projects[name_key]["challenges"]:
                return f"Challenge not found in project '{name}'."
            
            projects[name_key]["challenges"].remove(challenge)
            self.close_projects(projects, "data/projects.json")
            return f"Challenge removed from '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if old_challenge not in projects[name_key]["challenges"]:
                return f"Challenge not found in project '{name}'."
            
            idx = projects[name_key]["challenges"].index(old_challenge)
            projects[name_key]["challenges"][idx] = new_challenge
            self.close_projects(projects, "data/projects.json")
            return f"Challenge updated in '{name_key}'."



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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["technologies"].append(tech)
            self.close_projects(projects, "data/projects.json")
            return f"Technology '{tech}' added to '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if tech not in projects[name_key]["technologies"]:
                return f"Technology '{tech}' not found in project '{name}'."
            
            projects[name_key]["technologies"].remove(tech)
            self.close_projects(projects, "data/projects.json")
            return f"Technology '{tech}' removed from '{name_key}'."



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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["links"][label] = url
            self.close_projects(projects, "data/projects.json")
            return f"Link '{label}' added to '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if label not in projects[name_key]["links"]:
                return f"Link '{label}' not found in project '{name}'."
            
            projects[name_key]["links"][label] = new_url
            self.close_projects(projects, "data/projects.json")
            return f"Link '{label}' updated in '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if label not in projects[name_key]["links"]:
                return f"Link '{label}' not found in project '{name}'."
            
            del projects[name_key]["links"][label]
            self.close_projects(projects, "data/projects.json")
            return f"Link '{label}' removed from '{name_key}'."



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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            projects[name_key]["next_steps"].append(step)
            self.close_projects(projects, "data/projects.json")
            return f"Next step added to '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if step not in projects[name_key]["next_steps"]:
                return f"Next step not found in project '{name}'."
            
            projects[name_key]["next_steps"].remove(step)
            self.close_projects(projects, "data/projects.json")
            return f"Next step removed from '{name_key}'."

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
            name_key = name.upper().replace(" ", "_")
            projects = self.load_projects("data/projects.json")
            if name_key not in projects:
                return f"Project '{name}' not found."
            
            if old_step not in projects[name_key]["next_steps"]:
                return f"Next step not found in project '{name}'."
            
            idx = projects[name_key]["next_steps"].index(old_step)
            projects[name_key]["next_steps"][idx] = new_step
            self.close_projects(projects, "data/projects.json")
            return f"Next step updated in '{name_key}'."


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