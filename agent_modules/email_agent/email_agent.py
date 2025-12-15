"""
Email Agent
Monitors Gmail and alerts user about important emails.
"""

import base64
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, SQLiteSession

# Import our authentication helper
from gmail_auth import authenticate

load_dotenv()


# Keywords that indicate an important email
IMPORTANCE_KEYWORDS = [
    "assignment", "deadline", "exam", "urgent", "important", 
    "due date", "submit", "final", "midterm", "grade", "professor"
]


class EmailAgent:
    
    def __init__(self, name, instructions, model):
        self.name = name
        self.instructions = instructions
        self.model = model
        
        # Gmail services for each account
        self.gmail_services = {}
        
        # ========== ACCOUNT MANAGEMENT ==========
        
        @function_tool
        def connect_account(account_name: str):
            """
            Connect to a Gmail account. Must be called before accessing emails.
            Args:
                account_name: A label for this account (e.g., "personal", "school")
            Returns:
                Confirmation message with the connected email address.
            """
            service = authenticate(account_name)
            if service:
                self.gmail_services[account_name] = service
                # Get the email address for confirmation
                profile = service.users().getProfile(userId='me').execute()
                email = profile.get('emailAddress')
                return f"Connected to '{account_name}' account: {email}"
            return f"Failed to connect to '{account_name}' account."
        
        @function_tool
        def list_connected_accounts():
            """
            List all currently connected Gmail accounts.
            Returns:
                List of connected account names.
            """
            if not self.gmail_services:
                return "No accounts connected. Use connect_account() first."
            return f"Connected accounts: {list(self.gmail_services.keys())}"
        
        # ========== EMAIL RETRIEVAL ==========
        
        @function_tool
        def get_unread_emails(account_name: str, max_results: int = 10):
            """
            Get unread emails from a connected account.
            Args:
                account_name: The account to check (e.g., "personal", "school")
                max_results: Maximum number of emails to return (default 10)
            Returns:
                List of unread emails with subject, sender, and date.
            """
            if account_name not in self.gmail_services:
                return f"Account '{account_name}' not connected. Use connect_account() first."
            
            service = self.gmail_services[account_name]
            
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No unread emails in '{account_name}'."
            
            emails = []
            for msg in messages:
                email_data = self._get_email_summary(service, msg['id'])
                emails.append(email_data)
            
            return emails
        
        @function_tool
        def get_recent_emails(account_name: str, max_results: int = 10):
            """
            Get the most recent emails from a connected account.
            Args:
                account_name: The account to check
                max_results: Maximum number of emails to return (default 10)
            Returns:
                List of recent emails with subject, sender, and date.
            """
            if account_name not in self.gmail_services:
                return f"Account '{account_name}' not connected. Use connect_account() first."
            
            service = self.gmail_services[account_name]
            
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No emails found in '{account_name}'."
            
            emails = []
            for msg in messages:
                email_data = self._get_email_summary(service, msg['id'])
                emails.append(email_data)
            
            return emails
        
        @function_tool
        def search_emails(account_name: str, query: str, max_results: int = 10):
            """
            Search emails by query (same syntax as Gmail search).
            Args:
                account_name: The account to search
                query: Search query (e.g., "from:professor@uni.edu", "subject:assignment", "has:attachment")
                max_results: Maximum number of emails to return (default 10)
            Returns:
                List of matching emails.
            """
            if account_name not in self.gmail_services:
                return f"Account '{account_name}' not connected. Use connect_account() first."
            
            service = self.gmail_services[account_name]
            
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No emails found matching '{query}' in '{account_name}'."
            
            emails = []
            for msg in messages:
                email_data = self._get_email_summary(service, msg['id'])
                emails.append(email_data)
            
            return emails
        
        @function_tool
        def get_email_content(account_name: str, email_id: str):
            """
            Get the full content of a specific email.
            Args:
                account_name: The account containing the email
                email_id: The email's ID (from previous search results)
            Returns:
                Full email content including body.
            """
            if account_name not in self.gmail_services:
                return f"Account '{account_name}' not connected. Use connect_account() first."
            
            service = self.gmail_services[account_name]
            
            msg = service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            headers = msg.get('payload', {}).get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Get body
            body = self._get_email_body(msg)
            
            return {
                "id": email_id,
                "subject": subject,
                "from": sender,
                "date": date,
                "body": body
            }
        
        # ========== IMPORTANCE CHECKING ==========
        
        @function_tool
        def check_important_emails(account_name: str, max_results: int = 20):
            """
            Check for important unread emails based on keywords.
            Looks for: assignment, deadline, exam, urgent, important, etc.
            Args:
                account_name: The account to check
                max_results: Maximum number of emails to scan (default 20)
            Returns:
                List of emails flagged as important.
            """
            if account_name not in self.gmail_services:
                return f"Account '{account_name}' not connected. Use connect_account() first."
            
            service = self.gmail_services[account_name]
            
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No unread emails in '{account_name}'."
            
            important_emails = []
            for msg in messages:
                email_data = self._get_email_summary(service, msg['id'])
                
                # Check if subject contains importance keywords
                subject_lower = email_data['subject'].lower()
                sender_lower = email_data['from'].lower()
                
                for keyword in IMPORTANCE_KEYWORDS:
                    if keyword in subject_lower or keyword in sender_lower:
                        email_data['flagged_keyword'] = keyword
                        important_emails.append(email_data)
                        break
            
            if not important_emails:
                return f"No important emails found in '{account_name}'."
            
            return important_emails
        
        @function_tool
        def get_emails_from_sender(account_name: str, sender: str, max_results: int = 10):
            """
            Get emails from a specific sender.
            Args:
                account_name: The account to search
                sender: The sender's email or name to search for
                max_results: Maximum number of emails to return (default 10)
            Returns:
                List of emails from that sender.
            """
            return search_emails(account_name, f"from:{sender}", max_results)
        
        # Register all tools
        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=[
                connect_account, list_connected_accounts,
                get_unread_emails, get_recent_emails, search_emails,
                get_email_content, check_important_emails, get_emails_from_sender
            ],
            model=model
        )
    
    def _get_email_summary(self, service, msg_id):
        """Helper: Get email summary (subject, from, date)."""
        msg = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='metadata',
            metadataHeaders=['Subject', 'From', 'Date']
        ).execute()
        
        headers = msg.get('payload', {}).get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        
        return {
            "id": msg_id,
            "subject": subject,
            "from": sender,
            "date": date
        }
    
    def _get_email_body(self, msg):
        """Helper: Extract email body from message."""
        payload = msg.get('payload', {})
        
        # Simple case: body directly in payload
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        # Multipart case: look through parts
        parts = payload.get('parts', [])
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        
        # Fallback: try to find any text
        for part in parts:
            if 'body' in part and part['body'].get('data'):
                try:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                except:
                    pass
        
        return "(Could not extract email body)"


def get_instructions():
    """Generate instructions with current date."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"""
Personality: You are an AI agent that monitors Gmail accounts and alerts about important emails.

Purpose: To help the user stay on top of important emails without manually checking.

CURRENT DATE: {today}

Capabilities:
- Connect to multiple Gmail accounts (personal, school, etc.)
- Check for unread emails
- Search emails by sender, subject, or keywords
- Identify important emails (assignments, deadlines, exams, urgent matters)
- Read full email content when requested

Important Rules:
1. Before accessing emails, the account must be connected using connect_account().
2. When checking for important emails, look for keywords like: assignment, deadline, exam, urgent, important.
3. Always tell the user which account you're checking.
4. For privacy, only show email content when explicitly requested.
5. Use CURRENT DATE to understand relative dates like "yesterday", "last week", etc.

When reporting emails, format them clearly:
📧 Subject: [subject]
   From: [sender]
   Date: [date]
"""


def create_email_agent():
    """Factory function to create an EmailAgent instance."""
    return EmailAgent(
        name="EmailAgent",
        instructions=get_instructions(),
        model="gpt-4.1-mini"
    )


if __name__ == "__main__":
    email_agent = create_email_agent()
    session = SQLiteSession("EmailAgent Communication")

    async def main():
        print("Email Agent ready! Type 'quit' to exit.\n")
        print("First, connect an account: 'connect my personal gmail'\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            result = await Runner.run(
                starting_agent=email_agent.agent,
                input=user_input,
                session=session
            )
            print(f"\nAgent: {result.final_output}\n")

    asyncio.run(main())