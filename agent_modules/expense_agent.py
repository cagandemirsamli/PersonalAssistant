import json
import os
import time
import asyncio
from openai import OpenAI
from agents import Agent, Runner, function_tool, SQLiteSession

# Set the OpenAI API Key
api_key = input("Please enter the OpenAI API key: ")
os.environ["OPENAI_API_KEY"] = api_key

class ExpenseAgent():

    def __init__(self, name, instructions, model):
        self.name = name
        self.instructions = instructions
        self.model = model

        @function_tool
        def get_expenses():
            """
            Retrieve all expenses from the expense file.
            Returns:
                A list of all expenses with their details (category, date, amount)
            """
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            full_path = os.path.join(project_root, "data/expense_file.json")

            if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
                return "No expenses found."

            with open(full_path, 'r') as f:
                expenses = json.load(f)

            return expenses

        @function_tool
        def create_expense(category: str, date: str, amount: float):
            """
            Given expense features, create a dictionary storing them.
            Args:
                category: The category of the expense (str)
                date: The date of the expense as a string (str)
                amount: The amount spent (float)
            Returns:
                Confirmation message that the expense dictionary is successfully created.
            """
            try:
                print(f"Tool called with: category={category}, date={date}, amount={amount}")
                expense = {
                    "category": category,
                    "date": date,
                    "amount": amount
                }
                self.save_expense(expense=expense, save_dir="data/expense_file.json")
                print("Created successfully")
                return f"Expense dictionary correctly created"
            except Exception as e:
                print(f"Error in create_expense_tool: {e}")
                import traceback
                traceback.print_exc()
                return f"Error creating expense: {str(e)}"

        @function_tool
        def get_budgets():
            """
            Retrieve all budgets from the budget file.
            Returns:
                A dict of all budgets with their details (category, amount, spent)
            """
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            full_path = os.path.join(project_root, "data/budget_file.json")

            if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
                return "No budgets found."

            with open(full_path, 'r') as f:
                budgets = json.load(f)

            return budgets

        @function_tool
        def set_budget(category: str, amount: float, spent: float):
            try:
                print(f"Tool called with: category={category}, amount={amount}")
                budget = {
                    category: {
                        "amount": amount,
                        "spent": spent}
                }
                self.save_budget(budget=budget, save_dir="data/budget_file.json")
                print("Created successfully")
                return f"Expense dictionary correctly created"
            except Exception as e:
                print(f"Error in create_expense_tool: {e}")
                import traceback
                traceback.print_exc()
                return f"Error creating budget: {str(e)}"

        @function_tool
        def update_spendings(category: str, amount: float, budget_save_dir: str ="data/budget_file.json"):
            budgets = self.load_budgets(budget_save_dir)
            prev_spent = budgets[category]["spent"]
            budgets[category]["spent"] += amount
            self.close_budgets(budgets, save_dir="data/budget_file.json")
            return f"Previous spent: {prev_spent}, Updated spent: {budgets[category]['spent']}"

        @function_tool
        def edit_budget(category: str, amount: float, budget_save_dir: str = "data/budget_file.json"):
            budgets = self.load_budgets(budget_save_dir)
            prev_budget = budgets[category]
            budgets[category]["amount"] = amount
            self.close_budgets(budgets, save_dir="data/budget_file.json")
            return f"Previous budget: {prev_budget}, Updated budget: {budgets[category]}"

        @function_tool
        def remove_budget(category: str, budget_save_dir: str ="data/budget_file.json"):
            budgets = self.load_budgets(budget_save_dir)
            budgets.pop(category)
            self.close_budgets(budgets, save_dir="data/budget_file.json")
            return f"Budget successfully removed."


        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=[get_expenses, create_expense,
                   set_budget, update_spendings,
                   edit_budget, remove_budget],
            model=model
        )

    def save_expense(self, expense, save_dir):
        """
        Add an expense to the file that stores all expenses.
        Args:
            expense: The expense dictionary containing it's features (dict)
            save_dir: The directory where all of the expenses are stored (str)
        Returns:
            Confirmation message that the expense is successfully added to the file.
        """
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to project root, then join with save_dir
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Check if file exists and has content
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            try:
                with open(full_path, 'r') as f:
                    loaded_data = json.load(f)
                    # Convert list to dict if necessary (backward compatibility)
                    if isinstance(loaded_data, list):
                        expenses = {}
                        for idx, item in enumerate(loaded_data):
                            unique_key = f"{item.get('date', 'unknown')}_{item.get('category', 'unknown')}_{idx}"
                            expenses[unique_key] = item
                    else:
                        expenses = loaded_data
            except json.JSONDecodeError:
                # File exists but has invalid JSON, start fresh
                expenses = {}
        else:
            expenses = {}

        with open(full_path, "w") as f:
            json.dump(expenses, f, indent=4)
            print("Logged successfully")

        return f"Expense is logged in successfully!"

    def save_budget(self, budget, save_dir):
        """
        Add a budget to the file that stores all budgets.
        Args:
            budget: The budget dictionary containing it's features (dict)
            save_dir: The directory where all of the budgets are stored (str)
        Returns:
            Confirmation message that the budget is successfully added to the file.
        """

        budgets = self.load_budgets(save_dir="data/budget_file.json")
        budgets.update(budget)
        self.close_budgets(budgets=budgets, save_dir="data/budget_file.json")

        return f"Budget is logged in successfully!"

    def load_expenses(self, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            try:
                with open(full_path, 'r') as f:
                    loaded_data = json.load(f)
                    # Convert list to dict if necessary (backward compatibility)
                    if isinstance(loaded_data, list):
                        expenses = {}
                        for idx, item in enumerate(loaded_data):
                            unique_key = f"{item.get('date', 'unknown')}_{item.get('category', 'unknown')}_{idx}"
                            expenses[unique_key] = item
                    else:
                        expenses = loaded_data
            except json.JSONDecodeError:
                expenses = {}
        else:
            expenses = {}

        return expenses

    def close_expenses(self, expenses, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            json.dump(expenses, f, indent=4)
    def load_budgets(self, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            try:
                with open(full_path, 'r') as f:
                    budgets = json.load(f)
            except json.JSONDecodeError:
                budgets = {}
        else:
            budgets = {}

        return budgets

    def close_budgets(self, budgets, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            json.dump(budgets, f, indent=4)


instructions = """
Personality: You are an AI agent that keeps track of user expenses.

Purpose: To remind, alert, or complete other related tasks regarding user demand.

IMPORTANT: If the amount isn't entered, estimate it by comparing the average price in Turkey.
The currency is Turkish Lira (TL), nothing else.

Tip: Sometimes the amount might not be passed, in such cases it is your job to 
estimate the cost regarding the expense on average.
"""

expense_agent = ExpenseAgent(name="ExpenseAgent",
                             instructions=instructions,
                             model="gpt-4.1-mini")


session = SQLiteSession("ExpenseAgent Communication")
async def run_the_agent(agent):
    result = await Runner.run(
        starting_agent=agent,
        input=#"I want to create a new budget for coffee. I spent 150 tl on iced coffee on 19th November (add that to expenses as well). I haven't created a budget for the coffee category yet so create one with 2000 liras. Do the necessary things with these info."
        "can you record an expense of 200 tl on food for 20th november 2025",
        session=session
    )
    print(result.final_output)
    return result

asyncio.run(run_the_agent(expense_agent.agent))