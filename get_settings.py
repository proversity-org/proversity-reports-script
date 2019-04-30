import os
import json


def get_settings():

    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as config_file:
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
