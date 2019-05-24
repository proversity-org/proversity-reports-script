"""
Main module to get config settings from the config json file.
"""
import json
import os


def get_settings(should_set_environment_settings=False):
    """
    Returns and set environment settings in order to use them,
    during the report fecth and generation.

    Returns:
        Dict with the settings defined in the config file.
    """
    configuration_file_path = os.getenv('CONFIGURATION_FILE_PATH', None)

    if not configuration_file_path:
        print('Configuration file path was not provided.')
        exit()

    with open(configuration_file_path, 'r') as config_file:
        config_data = config_file.read()

    try:
        settings = json.loads(config_data)

        if should_set_environment_settings:
            set_environment_settings(settings)
    except ValueError as json_error:
        print(json_error.message)
        quit()

    return settings


def set_environment_settings(settings):
    """
    Set environment keys from config file.

    Args:
        settings: Settings dict from the config file.
    """
    os.environ['AWS_ACCESS_KEY_ID'] = settings.get('AWS_ACCESS_KEY_ID', '')
    os.environ['AWS_SECRET_ACCESS_KEY'] = settings.get('AWS_SECRET_ACCESS_KEY')
