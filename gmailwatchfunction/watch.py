from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def setup_gmail_watch(request):
    """Cloud Function to set up Gmail Watch."""
    # Load credentials from environment variables or Secret Manager
    creds = Credentials.from_authorized_user_file('client_secret.json')

    # Build the Gmail API service
    service = build('gmail', 'v1', credentials=creds)

    # Set up the watch
    watch_request = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/emailtobq/topics/newemail'
    }
    response = service.users().watch(userId='me', body=watch_request).execute()
    return f"Watch setup complete: {response}"
