"""
Main module to request and polling the report data.
"""

from importlib import import_module
from time import sleep

import requests

from proversity_reports_script.get_settings import get_settings  # pylint: disable=relative-import

SETTINGS = {}
report_backend = None


def init_report(report_name):
    """
    Init module to request the report generation.

    Args:
        report_name: String containing the requested report name from the cli command.
    """
    global report_backend
    global SETTINGS
    SETTINGS = get_settings()

    if not report_name in SETTINGS.get('SUPPORTED_REPORTS', []):
        print('Report is not suported.')
        exit()

    report_settings = SETTINGS.get(report_name.upper(), {})

    if not report_settings:
        print('Wrong report configuration.')
        exit()

    report_url = report_settings.get('REPORT_URL', '')

    report_backend = get_backend_report(report_settings)

    fetch_report_url(report_url)


def fetch_report_url(report_url):
    """
    Request the report generation.

    Args:
        report_url: API url endpoint to request the report generation take it from the
                    report configuration settings.
    """
    headers = {
        'Authorization': 'Bearer {}'.format(SETTINGS.get('OPEN_EDX_OAUTH_TOKEN')),
        'Content-Type': 'application/json',
    }
    request_url = '{lms_url}{report_url}'.format(
        lms_url=SETTINGS.get('LMS_URL'),
        report_url=report_url
    )
    courses = SETTINGS.get('COURSES', [])
    if not courses:
        print('Course id was not provided')
        exit()

    data = {}
    data.update({
        'course_ids': courses
    })

    response = requests.post(request_url, headers=headers, json=data)

    json_response = response.json()

    if response.status_code == 202:
        polling_report_data(json_response)
    else:
        print(response.status_code)


def polling_report_data(report_data_url):
    """
    Polling the report data in some configured unit times.

    Args:
        report_data_url: API url endpoint to request the report data.
    """
    polling_count = 0
    report_data = fetch_data_report(report_data_url)

    while(report_data.get('status') != 'SUCCESS'):
        # import ipdb; ipdb.set_trace()
        polling_count += 1
        sleep_for = 2 # every 2 seconds for 10 seconds

        if polling_count >= 5:
            sleep_for = 5 # then every 5 seconds for 20 seconds

        if polling_count >= 9:
            sleep_for = 15 # then every 15 seconds for for a minute

        if polling_count >= 13:
            sleep_for = 60 # then once a minute for 3

        if polling_count >= 16: # then stop
            print('Status failed to become success.')
            exit()

        if report_data.get('status') == 'FAILURE':
            print('Task failed...')
            exit()

        sleep(sleep_for)
        print('waitig for... {}'.format(sleep_for))
        report_data = fetch_data_report(report_data_url)

    print('Got it...')
    report_builder = report_backend()
    report_builder.json_report_to_csv(report_data)


def fetch_data_report(report_data_url):
    """
    Request for polling the report data.

    Args:
        report_data_url: API url endpoint to request the report data.
    Returns:
        The requests json reponse.
    """
    headers = {
        'Authorization': 'Bearer {}'.format(SETTINGS.get('OPEN_EDX_OAUTH_TOKEN')),
        'Content-Type': 'application/json'
    }
    request_url = '{report_url}'.format(
        report_url=report_data_url['state_url']
    )
    print('task id... {}'.format(report_data_url['state_url']))

    response = requests.get(request_url, headers=headers)
    json_response = {}

    print('status code... {}'.format(response.status_code))

    if response.status_code == 200:
        json_response = response.json()

    return json_response


def get_backend_report(report_settings):
    """
    Util function to get the configured report backend from the settings.
    """
    backend_module_name = report_settings.get('BACKEND_REPORT', '')

    if not backend_module_name:
        print('BACKEND_REPORT was not provided.')
        exit()

    module_string = backend_module_name.split(':')
    class_string = module_string[-1]
    backend = import_module(module_string[0])

    return getattr(backend, class_string)
