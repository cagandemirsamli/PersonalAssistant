import json
import os
import asyncio
from datetime import datetime
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

        # ========== EXPENSE FUNCTIONS ==========

        @function_tool
        def get_expenses(category: str = None):
            """
            Retrieve expenses, optionally filtered by category.
            Args:
                category: Optional category to filter by. If not provided, returns all expenses.
            Returns:
                Expenses matching the filter.
            """
            expenses = self.load_expenses("data/expense_file.json")
            if not expenses:
                return "No expenses found."
            
            if category:
                category_key = category.upper()
                if category_key not in expenses:
                    return f"No expenses found for category '{category}'."
                return {category_key: expenses[category_key]}
            
            return expenses

        @function_tool
        def add_expense(category: str, amount: float, date: str = None):
            """
            Add a new expense to a category.
            Args:
                category: The category of the expense (e.g., "coffee", "food", "transport")
                amount: The amount spent in TL
                date: The date of the expense (format: YYYY-MM-DD). Defaults to today.
            Returns:
                Confirmation message with budget status if a budget exists for this category.
            """
            category_key = category.upper()
            expense_date = date or datetime.now().strftime("%Y-%m-%d")
            
            expenses = self.load_expenses("data/expense_file.json")
            
            if category_key not in expenses:
                expenses[category_key] = []
            
            expenses[category_key].append({
                "date": expense_date,
                "amount": amount
            })
            
            self.close_expenses(expenses, "data/expense_file.json")
            
            # Check if there's a budget for this category and update spending
            budgets = self.load_budgets("data/budget_file.json")
            if category_key in budgets:
                budgets[category_key]["spent"] += amount
                self.close_budgets(budgets, "data/budget_file.json")
                
                limit = budgets[category_key]["amount"]
                spent = budgets[category_key]["spent"]
                remaining = limit - spent
                
                if remaining < 0:
                    return f"Expense of {amount} TL added to '{category}' on {expense_date}. ⚠️ OVER BUDGET! Spent {spent} TL of {limit} TL limit ({abs(remaining)} TL over)."
                elif remaining < limit * 0.2:
                    return f"Expense of {amount} TL added to '{category}' on {expense_date}. ⚠️ Warning: Only {remaining} TL remaining of {limit} TL budget."
                else:
                    return f"Expense of {amount} TL added to '{category}' on {expense_date}. Budget: {spent}/{limit} TL ({remaining} TL remaining)."
            
            return f"Expense of {amount} TL added to '{category}' on {expense_date}."

        @function_tool
        def remove_expense(category: str, date: str, amount: float = None):
            """
            Remove an expense from a category by matching date (and optionally amount).
            Args:
                category: The category of the expense
                date: The date of the expense to remove
                amount: Optional - the specific amount to match (useful if multiple expenses on same date)
            Returns:
                Confirmation or error message.
            """
            category_key = category.upper()
            expenses = self.load_expenses("data/expense_file.json")
            
            if not expenses or category_key not in expenses:
                return f"No expenses found for category '{category}'."
            
            original_count = len(expenses[category_key])
            removed_amount = 0
            
            if amount:
                # Remove specific expense matching date AND amount
                new_list = []
                removed = False
                for exp in expenses[category_key]:
                    if exp["date"] == date and exp["amount"] == amount and not removed:
                        removed_amount = exp["amount"]
                        removed = True  # Only remove first match
                    else:
                        new_list.append(exp)
                expenses[category_key] = new_list
            else:
                # Remove all expenses matching date
                new_list = [exp for exp in expenses[category_key] if exp["date"] != date]
                for exp in expenses[category_key]:
                    if exp["date"] == date:
                        removed_amount += exp["amount"]
                expenses[category_key] = new_list
            
            if len(expenses[category_key]) == original_count:
                return f"No expense found for '{category}' on {date}."
            
            self.close_expenses(expenses, "data/expense_file.json")
            
            # Update budget if exists
            budgets = self.load_budgets("data/budget_file.json")
            if category_key in budgets and removed_amount > 0:
                budgets[category_key]["spent"] = max(0, budgets[category_key]["spent"] - removed_amount)
                self.close_budgets(budgets, "data/budget_file.json")
            
            removed_count = original_count - len(expenses[category_key])
            return f"Removed {removed_count} expense(s) totaling {removed_amount} TL from '{category}'."

        @function_tool
        def get_category_total(category: str):
            """
            Get the total amount spent in a category.
            Args:
                category: The category to calculate total for
            Returns:
                Total amount spent in that category.
            """
            category_key = category.upper()
            expenses = self.load_expenses("data/expense_file.json")
            
            if not expenses or category_key not in expenses:
                return f"No expenses found for category '{category}'."
            
            total = sum(exp["amount"] for exp in expenses[category_key])
            count = len(expenses[category_key])
            
            return f"Category '{category}': {count} expense(s) totaling {total} TL."


        @function_tool
        def get_budgets():
            """
            Retrieve all budgets.
            Returns:
                A dict of all budgets with their limits and spending.
            """
            budgets = self.load_budgets("data/budget_file.json")
            if not budgets:
                return "No budgets found."
            return budgets

        @function_tool
        def get_budget(category: str):
            """
            Get budget details for a specific category.
            Args:
                category: The category to get budget for
            Returns:
                Budget details including limit, spent, and remaining.
            """
            category_key = category.upper()
            budgets = self.load_budgets("data/budget_file.json")
            
            if not budgets or category_key not in budgets:
                return f"No budget found for category '{category}'."
            
            budget = budgets[category_key]
            remaining = budget["amount"] - budget["spent"]
            percentage = (budget["spent"] / budget["amount"]) * 100 if budget["amount"] > 0 else 0
            
            return f"Budget '{category}': {budget['spent']}/{budget['amount']} TL ({percentage:.1f}% used, {remaining} TL remaining)."

        @function_tool
        def set_budget(category: str, amount: float):
            """
            Create a new budget for a category. Use edit_budget to modify existing budgets.
            Args:
                category: The category name for the budget (e.g., 'coffee', 'food', 'transport')
                amount: The budget limit for this category in TL
            Returns:
                Confirmation message.
            """
            category_key = category.upper()
            budgets = self.load_budgets("data/budget_file.json")
            
            if category_key in budgets:
                return f"Budget for '{category}' already exists with limit {budgets[category_key]['amount']} TL. Use edit_budget to modify it."
            
            # Calculate current spending from expenses
            expenses = self.load_expenses("data/expense_file.json")
            current_spent = 0
            if expenses and category_key in expenses:
                current_spent = sum(exp["amount"] for exp in expenses[category_key])
            
            budgets[category_key] = {
                "amount": amount,
                "spent": current_spent
            }
            
            self.close_budgets(budgets, "data/budget_file.json")
            
            if current_spent > 0:
                remaining = amount - current_spent
                return f"Budget for '{category}' created with {amount} TL limit. Current spending: {current_spent} TL ({remaining} TL remaining)."
            
            return f"Budget for '{category}' created with {amount} TL limit."

        @function_tool
        def edit_budget(category: str, new_amount: float):
            """
            Change the budget limit for an existing category.
            Args:
                category: The budget category to edit
                new_amount: The new budget limit in TL
            Returns:
                Confirmation showing previous and new limits.
            """
            category_key = category.upper()
            budgets = self.load_budgets("data/budget_file.json")
            
            if not budgets or category_key not in budgets:
                return f"No budget found for category '{category}'. Use set_budget to create one."
            
            prev_amount = budgets[category_key]["amount"]
            budgets[category_key]["amount"] = new_amount
            self.close_budgets(budgets, "data/budget_file.json")
            
            spent = budgets[category_key]["spent"]
            remaining = new_amount - spent
            
            return f"Budget for '{category}' updated: {prev_amount} → {new_amount} TL. Currently spent: {spent} TL ({remaining} TL remaining)."

        @function_tool
        def remove_budget(category: str):
            """
            Delete a budget category entirely.
            Args:
                category: The budget category to remove
            Returns:
                Confirmation message.
            """
            category_key = category.upper()
            budgets = self.load_budgets("data/budget_file.json")
            
            if not budgets or category_key not in budgets:
                return f"No budget found for category '{category}'."
            
            budgets.pop(category_key)
            self.close_budgets(budgets, "data/budget_file.json")
            
            return f"Budget for '{category}' removed."

        @function_tool
        def reset_budget_spending(category: str):
            """
            Reset the spent amount to 0 for a budget category (e.g., at start of new month).
            Args:
                category: The budget category to reset
            Returns:
                Confirmation message.
            """
            category_key = category.upper()
            budgets = self.load_budgets("data/budget_file.json")
            
            if not budgets or category_key not in budgets:
                return f"No budget found for category '{category}'."
            
            prev_spent = budgets[category_key]["spent"]
            budgets[category_key]["spent"] = 0
            self.close_budgets(budgets, "data/budget_file.json")
            
            return f"Budget '{category}' spending reset: {prev_spent} → 0 TL."

        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=[
                get_expenses, add_expense, remove_expense, get_category_total,
                get_budgets, get_budget, set_budget, edit_budget, remove_budget, reset_budget_spending
            ],
            model=model
        )

    def load_expenses(self, save_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_path = os.path.join(project_root, save_dir)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            try:
                with open(full_path, 'r') as f:
                    expenses = json.load(f)
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


def get_instructions():
    """Generate instructions with current date."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"""
Personality: You are an AI agent that keeps track of user expenses and budgets.

Purpose: To record expenses, manage budgets per category, alert users about spending limits, 
and complete other related tasks regarding user demand.

CURRENT DATE: {today}

Capabilities:
EXPENSES:
- Add expenses with category, amount, and date
- View all expenses or filter by category
- Remove expenses by category and date
- Get total spending per category

BUDGETS:
- Create budgets with spending limits per category
- View budget status (limit, spent, remaining)
- Edit budget limits
- Reset spending (for new month)
- Automatic budget tracking when adding expenses

Important Rules:
1. If the date isn't provided, use today's date (CURRENT DATE above).
2. If the amount isn't provided, ask the user to specify it.
3. The currency is Turkish Lira (TL).
4. When adding an expense, automatically update the budget if one exists for that category.
5. Alert the user when spending exceeds 80% of budget or goes over limit.
6. Use CURRENT DATE to calculate relative dates like "today", "yesterday", etc.
"""


def create_expense_agent():
    """Factory function to create an ExpenseAgent instance."""
    return ExpenseAgent(
        name="ExpenseAgent",
        instructions=get_instructions(),
        model="gpt-4.1-mini"
    )


if __name__ == "__main__":
    expense_agent = create_expense_agent()
    session = SQLiteSession("ExpenseAgent Communication")

    async def main():
        print("Expense Agent ready! Type 'quit' to exit.\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            result = await Runner.run(
                starting_agent=expense_agent.agent,
                input=user_input,
                session=session
            )
            print(f"\nAgent: {result.final_output}\n")

    asyncio.run(main())
