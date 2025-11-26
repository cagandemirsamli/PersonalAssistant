import json
import os
import asyncio
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
        def set_deadlines():
            """
            Sets a new deadline regarding an assignment.
            Returns:
                A completion message that the deadline is correctly added.
            """

