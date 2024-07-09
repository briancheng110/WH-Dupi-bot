from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import pickle
import os.path
import os
import pandas as pd
import base64

def create_draft(service, recipient, message_text):
    """
    Create and insert a draft email with the given message text.
    
    :param service: Authorized Gmail API service instance.
    :param recipient: Reciever
    :param message_text: Text to be included in the draft message.
    :return: Draft object if created successfully, None otherwise.
    """
    try:
        # Create a MIMEText object
        message = MIMEText(message_text)
        message['to'] = recipient  # Drafts don't technically need a recipient, but you can specify one
        message['subject'] = 'Draft created via Gmail API'
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Create a draft
        draft_body = {'message': {'raw': raw_message}}
        draft = service.users().drafts().create(userId='brian.cheng53@gmail.com', body=draft_body).execute()
        
        print(f"Draft ID: {draft['id']} created.")
        return draft
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

    print(f"An error occurred creating the draft: {e}")

def get_google_service(api_name, api_version, scopes, client_secrets_file='credentials.json'):
    """
    Creates a Google API service.

    Parameters:
    - api_name: Name of the API (e.g., 'calendar').
    - api_version: Version of the API (e.g., 'v3').
    - scopes: A list of strings representing the OAuth scopes needed for the service.
    - client_secrets_file: Path to the client secrets JSON file. Defaults to 'credentials.json'.

    Returns:
    - A resource object with methods for interacting with the service.
    """
    creds = None
    token_pickle_file = f'C:\\Users\\dao3312\\OneDrive - Northwestern University\\Desktop\\WorkHelper\\Secrets\\token_{api_name}.pickle'

    # Check if token pickle file exists for the API, which stores the user's access and refresh tokens.
    if os.path.exists(token_pickle_file):
        with open(token_pickle_file, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_pickle_file, 'wb') as token:
            pickle.dump(creds, token)

    service = build(api_name, api_version, credentials=creds)
    return service


if __name__ == "__main__":
    data_file = "C:\\Users\\dao3312\\OneDrive - Northwestern University\\Desktop\\WorkHelper\\Secrets\\Dupi itch subjects.xlsx"
    sheet_to_read = 1  # Change to sheet name (string) if needed
    df = read_xlsx(data_file, sheet_name=sheet_to_read)

    if df is not None:
        # Process the DataFrame object
        print(df.head())  # Print the first few rows
    else:
        print("An error occurred while reading the file.")

    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    gmail_service_handle = get_google_service('gmail', 'v1', SCOPES)
    template_str = read_text_file("C:\\Users\\dao3312\\OneDrive - Northwestern University\\Desktop\\WorkHelper\\Weekly nag.txt")

    test = find_subjects_due_today(df)
    num_subject = len(test)
    print(test)

    for index, row in test.iterrows():
        replacements = {
            "proxy_name": row['proxy_name'],
            "first_name": row['first_name'],
            "child_survey": "https://example.com/child_survey",
            "proxy_survey": "https://example.com/proxy_survey",
            "next_visit_date": row['next_visit_date'],
            "visit_type": row['visit_type'].lower(),
            "outstanding_items": "None"
        }
        print(replacements)
        message = customize_message(template_str, replacements)
        print(message)
        create_draft(gmail_service_handle, '18037927008.18033702222.6-47HfMCV-@txt.voice.google.com', message)
