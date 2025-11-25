import json
import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, SQLiteSession

# Load environment variables from .env file
load_dotenv()
# The agents library uses OPENAI_API_KEY from the environment automatically

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
        def delete_expense(category: str, date: str):
            """
            Delete an expense by matching its category and date.
            Args:
                category: The category of the expense to delete
                date: The date of the expense to delete
            Returns:
                Confirmation message or error if expense not found.
            """
            try:
                expenses = self.load_expenses("data/expense_file.json")
                if not expenses:
                    return "No expenses found to delete."
                
                # Find and remove matching expense(s)
                keys_to_delete = [
                    key for key, exp in expenses.items()
                    if exp.get("category", "").lower() == category.lower()
                    and exp.get("date", "").lower() == date.lower()
                ]
                
                if not keys_to_delete:
                    return f"No expense found for category '{category}' on date '{date}'."
                
                for key in keys_to_delete:
                    del expenses[key]
                
                self.close_expenses(expenses, save_dir="data/expense_file.json")
                return f"Deleted {len(keys_to_delete)} expense(s) for '{category}' on {date}."
            except Exception as e:
                return f"Error deleting expense: {str(e)}"

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
        def set_budget(category: str, amount: float, spent: float = 0.0):
            """
            Create or update a budget for a specific category.
            Args:
                category: The category name for the budget (e.g., 'coffee', 'food', 'transport')
                amount: The total budget limit for this category
                spent: The amount already spent in this category (default 0.0 for new budgets)
            Returns:
                Confirmation message that the budget was created/updated.
            """
            try:
                print(f"Tool called with: category={category}, amount={amount}")
                budget = {
                    category: {
                        "amount": amount,
                        "spent": spent}
                }
                self.save_budget(budget=budget, save_dir="data/budget_file.json")
                print("Created successfully")
                return f"Budget for '{category}' created with limit {amount} TL"
            except Exception as e:
                print(f"Error in set_budget: {e}")
                import traceback
                traceback.print_exc()
                return f"Error creating budget: {str(e)}"

        @function_tool
        def update_spendings(category: str, amount: float):
            """
            Add spending amount to an existing budget category.
            Args:
                category: The budget category to update
                amount: The amount spent to add to the category's total spending
            Returns:
                Message showing the previous and updated spending amounts.
            """
            try:
                budgets = self.load_budgets("data/budget_file.json")
                if category not in budgets:
                    return f"No budget found for category '{category}'. Create one first with set_budget."
                prev_spent = budgets[category]["spent"]
                budgets[category]["spent"] += amount
                self.close_budgets(budgets, save_dir="data/budget_file.json")
                limit = budgets[category]["amount"]
                new_spent = budgets[category]["spent"]
                remaining = limit - new_spent
                return f"Updated '{category}' spending: {prev_spent} → {new_spent} TL (limit: {limit} TL, remaining: {remaining} TL)"
            except Exception as e:
                return f"Error updating spendings: {str(e)}"

        @function_tool
        def edit_budget(category: str, amount: float):
            """
            Change the budget limit for an existing category.
            Args:
                category: The budget category to edit
                amount: The new budget limit amount
            Returns:
                Message showing the previous and updated budget limits.
            """
            try:
                budgets = self.load_budgets("data/budget_file.json")
                if category not in budgets:
                    return f"No budget found for category '{category}'. Create one first with set_budget."
                prev_amount = budgets[category]["amount"]
                budgets[category]["amount"] = amount
                self.close_budgets(budgets, save_dir="data/budget_file.json")
                return f"Updated '{category}' budget limit: {prev_amount} → {amount} TL"
            except Exception as e:
                return f"Error editing budget: {str(e)}"

        @function_tool
        def remove_budget(category: str):
            """
            Delete a budget category entirely.
            Args:
                category: The budget category to remove
            Returns:
                Confirmation that the budget was removed.
            """
            try:
                budgets = self.load_budgets("data/budget_file.json")
                if category not in budgets:
                    return f"No budget found for category '{category}'."
                budgets.pop(category)
                self.close_budgets(budgets, save_dir="data/budget_file.json")
                return f"Budget for '{category}' successfully removed."
            except Exception as e:
                return f"Error removing budget: {str(e)}"


        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=[get_expenses, create_expense, delete_expense,
                   get_budgets, set_budget, update_spendings,
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

        # Generate a unique key and add the new expense
        unique_key = f"{expense.get('date', 'unknown')}_{expense.get('category', 'unknown')}_{len(expenses)}"
        expenses[unique_key] = expense

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
Personality: You are an AI agent that keeps track of user expenses and budgets.

Purpose: To record expenses, manage budgets per category, alert users about spending limits, 
and complete other related tasks regarding user demand.

CAPABILITIES:
- Record and retrieve expenses (category, date, amount)
- Create, update, and remove budgets per category
- Track spending against budget limits
- Alert when spending approaches or exceeds budget limits

IMPORTANT RULES:
1. If the amount isn't entered, estimate it by comparing the average price in Turkey.
2. The currency is Turkish Lira (TL), nothing else.
3. When adding an expense to a category that has a budget, also update the budget spending.
4. Always inform the user of their remaining budget after recording an expense.
"""

def create_expense_agent():
    """Factory function to create an ExpenseAgent instance."""
    return ExpenseAgent(
        name="ExpenseAgent",
        instructions=instructions,
        model="gpt-4.1-mini"
    )


# Only run when executed directly, not when imported
if __name__ == "__main__":
    expense_agent = create_expense_agent()
    session = SQLiteSession("ExpenseAgent Communication")

    async def run_the_agent(agent):
        result = await Runner.run(
            starting_agent=agent,
            input="I spent 170 tl on iced coffee on 24th November (add to expense list as well). If I haven't created a budget for coffee yet, create one with 2000 liras. If there is an existing coffee budget, let me know of the limit and how much I spent up to this point.",
            session=session
        )
        print(result.final_output)
        return result

    asyncio.run(run_the_agent(expense_agent.agent))