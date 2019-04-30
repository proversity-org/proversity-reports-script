import os
import json


def get_settings():

    configuration_file_path = os.getenv('CONFIGURATION_FILE_PATH', None)

    if not configuration_file_path:
        print('Configuration file path was not provided.')
        exit()

    with open(configuration_file_path, 'r') as config_file:
        config_data = config_file.read()

    try:
        settings = json.loads(config_data)
        set_environment_settings(settings)
    except ValueError as json_error:
        quit()

    return settings


def set_environment_settings(settings):
    os.environ['AWS_ACCESS_KEY_ID'] = settings.get('AWS_ACCESS_KEY_ID', '')
    os.environ['AWS_SECRET_ACCESS_KEY'] = settings.get('AWS_SECRET_ACCESS_KEY')
