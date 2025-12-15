import os
import pickle

# Google authentication libraries
from google.auth.transport.requests import Request       # For refreshing expired tokens
from google.auth.exceptions import RefreshError          # For handling refresh failures
from google_auth_oauthlib.flow import InstalledAppFlow   # For running the OAuth browser flow
from googleapiclient.discovery import build              # For building the Gmail service

# SCOPE: What permission are we asking for?
# gmail.readonly = can read emails, but CANNOT send, delete, or modify
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_credentials_path():
    """
    Get the path to client_secret.json.
    Returns the file path (not contents) because Google's library parses it.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))        # → email_agent/
    agent_modules_dir = os.path.dirname(script_dir)                 # → agent_modules/
    project_root = os.path.dirname(agent_modules_dir)               # → PersonalAssistant/
    
    credentials_dir = os.path.join(project_root, "data", "email_credentials")
    client_secret_path = os.path.join(credentials_dir, "client_secret.json")
    
    if not os.path.exists(client_secret_path):
        print(f"ERROR: client_secret.json not found at {client_secret_path}")
        return None
    
    return client_secret_path


def get_token_path(account_name: str):
    """
    Get the path where we'll save/load the token for a specific account.
    Each account gets its own token file (e.g., personal_token.pickle, school_token.pickle)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    agent_modules_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(agent_modules_dir)
    
    credentials_dir = os.path.join(project_root, "data", "email_credentials")
    token_path = os.path.join(credentials_dir, f"{account_name}_token.pickle")
    
    return token_path


def authenticate(account_name: str):
    """
    Authenticate with Gmail and return a service object.
    
    Args:
        account_name: Label for this account (e.g., "personal", "school")
    
    Returns:
        Gmail API service object, or None if authentication fails.
    """
    
    # Get file paths
    client_secret_path = get_credentials_path()
    token_path = get_token_path(account_name)
    
    if not client_secret_path:
        return None  # client_secret.json not found
    
    creds = None
    
    # =========================================
    # STEP 1: Check if we have a saved token
    # =========================================
    if os.path.exists(token_path):
        print(f"Found existing token for '{account_name}', loading...")
        with open(token_path, 'rb') as f:      # 'rb' = read binary (pickle format)
            creds = pickle.load(f)
    
    # =========================================
    # STEP 2: Validate the token
    # =========================================
    if creds and creds.valid:
        # Token exists and is still valid - we're good!
        print(f"Token for '{account_name}' is valid.")
    
    elif creds and creds.expired and creds.refresh_token:
        # Token expired but we can try to refresh it (no browser needed)
        print(f"Token for '{account_name}' expired, attempting to refresh...")
        try:
            creds.refresh(Request())
            # Save the refreshed token
            with open(token_path, 'wb') as f:
                pickle.dump(creds, f)
            print("Token refreshed and saved.")
        except RefreshError as e:
            # Refresh failed - token was revoked or can't be refreshed
            print(f"Token refresh failed: {e}")
            print("Need to re-authenticate...")
            creds = None  # Set to None so we fall through to re-authentication
    
    # Check again if we need to authenticate (either no creds or refresh failed)
    if not creds or not creds.valid:
        # No token or can't refresh - need user to log in via browser
        print(f"\n{'='*50}")
        print(f"LOGIN REQUIRED for '{account_name}'")
        print(f"{'='*50}")
        print("A browser window will open.")
        print("Please log in with your Gmail account and click 'Allow'.")
        print(f"{'='*50}\n")
        
        # This is the magic line - opens browser for OAuth
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the new token so user doesn't have to log in next time
        with open(token_path, 'wb') as f:
            pickle.dump(creds, f)
        print(f"Token saved for '{account_name}'.")
    
    # =========================================
    # STEP 3: Build the Gmail service
    # =========================================
    # Now that we have valid credentials, create the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    print(f"Gmail service ready for '{account_name}'!")
    
    return service


# ============================================================
# TEST: Run this file directly to test authentication
# ============================================================
if __name__ == "__main__":
    print("="*50)
    print("GMAIL AUTHENTICATION TEST")
    print("="*50)
    
    # Ask user which account to authenticate
    account = input("\nEnter account name (e.g., 'personal' or 'school'): ").strip()
    
    if not account:
        account = "test"
    
    print(f"\nAuthenticating '{account}'...")
    service = authenticate(account)
    
    if service:
        # Test the connection by getting user's email address
        print("\nTesting connection...")
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        print(f"✓ SUCCESS! Connected to: {email}")
    else:
        print("✗ Authentication failed!")
