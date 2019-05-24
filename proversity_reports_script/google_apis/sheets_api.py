"""
Main module to get access to the Google Sheets API.
"""
import csv
import json
import os

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from get_google_oauth_permissions import credentials_to_dict


def get_sheets_api_service():
    """
    Returns the Google Sheet API service.

    Attempts to get the Google oAuth credentials from the provided file.

    Returns:
        None if some problem to get the service is raised.
        spreadsheets() service object.
    """
    oauth_file_path = os.getenv('OAUTH_CONFIGURATION_FILE', None)

    if not oauth_file_path:
        print('oAuth config file was not provided.')
        return None

    google_oauth_credentials = get_settings_from_file(oauth_file_path)

    if not google_oauth_credentials:
        print('Google oAuth settings were not provided.')
        return None

    try:
        oauth_credentials = Credentials(**google_oauth_credentials)
    except GoogleAuthError as goo_error:
        print('Unable to create the Credentials object. {}'.format(goo_error.message))
        return None

    if not oauth_credentials or not oauth_credentials.valid:
        if oauth_credentials and oauth_credentials.expired and oauth_credentials.refresh_token:
            oauth_credentials.refresh(Request())

            print('Google oAuth credentials are being updated.')

            # Save the credentials for the next run.
            credentials_data = credentials_to_dict(oauth_credentials)

            with open(oauth_file_path, 'w') as json_file:
                json.dump(credentials_data, json_file, sort_keys=True)
                print('Google oAuth credentials were updated.')
        else:
            print('The credentials cannot be obtained or token has expired.')
            return None

    sheet_api = None

    try:
        sheets_service = build('sheets', 'v4', credentials=oauth_credentials)
        sheet_api = sheets_service.spreadsheets()
    except Exception as error:  # pylint: disable=broad-except
        print('Unable to build or obtain the Google Sheets service. {}'.format(error.message))
        return None

    return sheet_api


def get_settings_from_file(file_path):
    """
    Retrives the oAuth credentials dict from a file.

    Args:
        file_path: oAuth credentials file path.
    Returns:
        credentials json object from file.
        None: if the data cannot be parsed into json format.
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


def get_data_from_csv(file_path):
    """
    Reads the csv and returns its data as a list.

    Args:
        file_path: csv file path.
    Returns:
        List containing all rows in the csv file.
    """
    csv_data = []

    if os.path.exists(file_path):
        with open(file_path, 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')

            for row in spamreader:
                csv_data.append(row)
    else:
        print('The csv file does not exists. {}'.format(file_path))
    return csv_data


def update_sheets_data(file_path, spreadsheet_id):
    """
    Updates the report data on the provided spreadsheet id.

    Google Sheets reference: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values

    Args:
        file_path: Report file data path.
        spreadsheet_id: Google Sheet report ID.
    Returns:
        None: if there is a problem updating the report.
    """
    csv_data = get_data_from_csv(file_path)

    if not csv_data:
        print('The report data is empty and it was not updated on Google Sheets.')
        return None

    if not spreadsheet_id:
        print('Spreadsheet id was not provided and the report cannot be updated on Google Sheets.')
        return None

    # Updates all the spreadsheet.
    range_name = 'Sheet1'
    value_input_option = 'USER_ENTERED'
    body = {
        'values': csv_data
    }
    api_service = get_sheets_api_service()

    if not api_service:
        print('Unable to obtain the Google Sheets API service, the report was not updated.')
        return None

    try:
        api_service.values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        ).execute()

        api_service.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body,
        ).execute()
    except Exception as error:
        print('There was an error updating report on Google Sheet. {}'.format(error.message))
        return None

    print('The report data was successfully updated on Google Sheets.')
