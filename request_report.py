import requests
from time import sleep
import csv
import boto3
from importlib import import_module
import json

from get_settings import get_settings

SETTINGS = {}
report_backend = None

def init_report(report_name):

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
    headers = {
        'Authorization': 'Bearer {}'.format(SETTINGS.get('OPEN_EDX_OAUTH_TOKEN')),
        'Content-Type': 'application/json',
    }
    request_url = '{lms_url}{report_url}'.format(
        lms_url=SETTINGS.get('LMS_URL'),
        report_url=report_url
    )
    data = {
        'course_ids': [
            'course-v1:GCS+GCS001+2018'
        ]
    }

    response = requests.post(request_url, headers=headers, json=data)

    json_response = response.json()

    if response.status_code == 202:
        polling_report_data(json_response)
    else:
        print(response.status_code)


def polling_report_data(report_data_url):

    polling_count = 0
    report_data = fetch_data_report(report_data_url)

    while (report_data.get('status') != "SUCCESS"):
        polling_count += 1
        sleep_for = 2 # every 2 seconds for 10 seconds

        if polling_count >= 5:
            sleep_for = 5 # then every 5 seconds for 20 seconds

        if polling_count >= 9:
            sleep_for = 15 # then every 15 seconds for for a minute

        if polling_count >= 13:
            sleep_for = 60 # then once a minute for 3

        if polling_count >= 16: # then stop
            print("Status failed to become success")
            exit()

        sleep(sleep_for)
        report_data = fetch_data_report(report_data_url)

    report_builder = report_backend()
    report_builder.json_report_to_csv(report_data)


def fetch_data_report(report_data_url):
    headers = {
        'Authorization': 'Bearer {}'.format(SETTINGS.get('OPEN_EDX_OAUTH_TOKEN'))
    }
    request_url = '{report_url}'.format(
        report_url=report_data_url["state_url"]
    )

    response = requests.get(request_url, headers=headers)
    json_response = {}

    if response.status_code == 200:
        json_response = response.json()

    return json_response


def get_backend_report(report_settings):
    backend_module_name = report_settings.get('BACKEND_REPORT', '')

    if not backend_module_name:
        print('BACKEND_REPORT was not provided.')
        exit()

    module_string = backend_module_name.split(":")
    class_string = module_string[-1]
    backend = import_module(module_string[0])

    return getattr(backend, class_string)
