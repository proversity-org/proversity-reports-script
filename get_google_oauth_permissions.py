"""
This file is intended to get the Google oAuth permissions,
in order to use the Google Sheet API.

This file must be run on local machine with access to
an browser window, since this command opens a new browser tab to
get the user consent from the Google user.

This is a one time operation to give those user permission to the
provided Google oAuth credentials (client-id and client-secret).
"""
from argparse import ArgumentParser
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

from proversity_reports_script.get_settings import get_settings

# SCOPE for read, create, delete and update Google Spreadsheets data.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
REQUIRED_CREDENTIALS = [
    'token', 'refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes',
]


def main():
    """
    Opens a new tab browser to get the user consent permission to
    read and update his Google Sheet data.
    """
    parser = ArgumentParser()
    parser.add_argument('--config-file', '-c', help='Path to configuration file.', required=True)
    args = parser.parse_args()

    os.environ['CONFIGURATION_FILE_PATH'] = args.config_file

    global_settings = get_settings(should_set_environment_settings=False)
    google_oauth_credentials = global_settings.get('GOOGLE_OAUTH_CREDENTIALS', None)

    if not google_oauth_credentials:
        print('Google oAuth credentials were not provided.')
        exit()

    try:
        flow = InstalledAppFlow.from_client_config(
            google_oauth_credentials,
            SCOPES
        )

        credentials = flow.run_local_server()

        if not credentials:
            raise GoogleApiCredentialsError('Credentials object is empty.')

        credentials_data = credentials_to_dict(credentials)

        with open('google-oauth-credentials.json', 'w') as json_file:
            json.dump(credentials_data, json_file, sort_keys=True)

    except Exception as error:
        raise error


def credentials_to_dict(credentials):
    """
    Returns a dict object with the required information.

    Args:
        credentials: google.oauth2.credentials.Credentials Object.
    Returns:
        Dict object containing the required data such as token, refresh_token...
    Raises:
        GoogleApiCredentialsError: When some of the required fields is missing from the credentials object.
    """
    required_data = {}

    for field in REQUIRED_CREDENTIALS:
        credential_field = getattr(credentials, field, None)

        if not credential_field:
            error_message = 'Credential field is missing. {}'.format(field)
            raise GoogleApiCredentialsError(error_message)

        required_data.update({
            field: credential_field
        })

    return required_data


class GoogleApiCredentialsError(Exception):
    """
    Exception class raised when a Google oAuth credentials
    is missing, empty, or there is other problem related to Google credentials object.
    """
    pass


if __name__ == '__main__':
    main()
