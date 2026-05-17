# Gmail OAuth helper - CS 153 Frontier Systems
# Handles the OAuth 2.0 flow for a Google "Desktop app" client.
#
# First run:  opens a browser window to log in and grant access,
#             then saves the resulting token to token.json.
# Later runs: reuses token.json (refreshing it automatically when
#             the access token has expired).

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only access: this app can read mail but never send or delete.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_credentials():
    """Return valid OAuth credentials, running the login flow if needed."""
    creds = None

    # Reuse a previously saved token if one exists.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there's no valid token, refresh it or run the browser login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' not found. Download the OAuth "
                    "desktop client file from Google Cloud Console and "
                    "place it next to this script."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            # Opens a browser window and starts a local server to
            # capture the OAuth redirect.
            creds = flow.run_local_server(port=0)

        # Save the token so future runs skip the browser step.
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


def get_gmail_service():
    """Return an authenticated Gmail API service object."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)
