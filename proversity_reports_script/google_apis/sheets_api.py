"""
Main module to get access to the Google Sheets API.
"""
import json
import os

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from proversity_reports_script.get_google_oauth_permissions import GoogleApiCredentialsError


def get_sheets_api_service():
    """
    Returns the Google Sheet API service.
    """
    oauth_file_path = os.getenv('OAUTH_CONFIGURATION_FILE', None)
    # oauth_file_path = '/data/proversity/ironwood/scripts/report-scripts/google-oauth-credentials.json'

    if not oauth_file_path:
        print('oAuth config file was not provided.')
        return None

    google_oauth_credentials = get_settings_from_file(oauth_file_path)

    if not google_oauth_credentials:
        print('Google oauth settings were not provided.')
        return None

    oauth_credentials = Credentials(**google_oauth_credentials)

    if not oauth_credentials or not oauth_credentials.valid:
        if oauth_credentials and oauth_credentials.expired and oauth_credentials.refresh_token:
            oauth_credentials.refresh(Request())
            # TO-DO Write new credentials to config file.
        else:
            print('The credentials cannot be obtained or updated.')
            return None

    sheet_api = None

    try:
        sheets_service = build('sheets', 'v4', credentials=oauth_credentials)
        sheet_api = sheets_service.spreadsheets()
    except Exception as error:  # pylint: disable=broad-except
        GoogleApiCredentialsError(error.message)

    return sheet_api


def get_settings_from_file(file_path):
    """
    Retrives the oAuth credentials idct form a file.
    """
    credentials = {}

    if os.path.exists(file_path):
        with open(file_path, 'r') as credentials_file:
            try:
                credentials = json.loads(credentials_file.read())
            except ValueError:
                print('oAuth config file contents cannot be parsed into json.')
                return None

    return credentials


# some = get_sheets_api_service()
# import ipdb; ipdb.set_trace()
# print(some)

# class GoogleApiCredentialsError(Exception):
#     """
#     Exception class raised when a Google oAuth credentials
#     is missing, empty, or there is other problem related to Google credentials object.
#     """
#     pass
