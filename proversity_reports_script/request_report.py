"""
Main module to request and polling the report data.
"""

from importlib import import_module
from time import sleep

from proversity_reports_script.get_settings import get_settings
from proversity_reports_script.request_module import request_handler
from proversity_reports_script.report_apis.report_api_v1 import (
    get_report_generation_data as get_report_generation_data_v1,
)


class FetchReportData(object):
    """
    Fetch and initialize the report backend.
    """
    def __init__(self, *args, **kwargs):
        self.settings = get_settings(should_set_environment_settings=True)
        self.command_extra_arguments = kwargs.pop('extra_arguments', {})
        self.api_version = kwargs.pop('api_version', 'v0')

        self.courses = self.settings.get('COURSES', [])

        if not self.courses:
            print('Course id list was not provided.')
            exit()

        report_name = kwargs.pop('report_name', '')

        if not report_name in self.settings.get('SUPPORTED_REPORTS', []):
            print('Report is not configured.')
            exit()

        self.report_settings = self.settings.get(report_name.upper(), {})

        if not self.report_settings:
            print('Missing report configuration.')
            exit()

        self.report_backend = get_backend_report(self.report_settings)

    def init_report_pipeline(self, *args, **kwargs):
        """
        Initialize the report pipeline to fetch the report data
        and then initialize the appropriate report backend.
        """
        self.init_report_backend(
            report_data=self.get_report_data(
                report_generation_request_response=self.get_report_generation_data(),
                request_headers=self.get_request_headers(),
            )
        )

    def get_report_generation_data(self):
        """
        Return the response data from the report generation request.

        Since API v0 does not support paging, it returns the plain response data.

        For API v1, to avoid requesting data for a large set of courses (and probably get a 504 error),
        the report generation request is divided into groups of courses
        determined by EXTRA_DATA['MAX_COURSES_PER_REQUEST'] from the report configuration.
        Each response data is collected into one object.

        Returns:
            v0:
                {
                    "message": "The task with id = {task id} has been initialize.",
                    "state_url": "http://lms-domain/proversity-reports/api/v0/get-report-data?task_id={task id}",
                    "success": true
                }
            v1:
                {
                    "data": [
                        "course-id-0": [
                            "http://lms-domain/proversity-reports/api/v1/get-report-data?task_id={task id}"
                        ],
                        "course-id-1": [
                            "http://lms-domain/proversity-reports/api/v1/get-report-data?task_id={task id}"
                            "http://lms-domain/proversity-reports/api/v1/get-report-data?task_id={task id}"
                        ]...
                    ]
                }
        """
        initial_report_request_url, report_generation_request_data = self.report_generation_request_data()
        extra_request_data = self.report_settings.get('EXTRA_REQUEST_DATA', {})

        if not initial_report_request_url:
            print('Report URL was not provided.')
            exit()

        if self.api_version == 'v0':
            print('Report generation requested to: {}'.format(initial_report_request_url))

            return request_handler(
                request_url=initial_report_request_url,
                request_data=report_generation_request_data,
                request_type='POST',
                request_headers=self.get_request_headers(),
                query_params=extra_request_data.get('query_params', {}),
            )

        if self.api_version == 'v1':
            return get_report_generation_data_v1(
                request_data=report_generation_request_data,
                request_url=initial_report_request_url,
                extra_request_data=extra_request_data,
                report_settings=self.report_settings,
                request_headers=self.get_request_headers(),
            )

    def report_generation_request_data(self):
        """
        Return the report generation request url and data.

        Returns:
            request_url: URL of the generation report API endpoint.
            request_data: Dict that contains the request body.
        """
        request_url = '{lms_url}{report_url}'.format(
            lms_url=self.settings.get('LMS_URL', ''),
            report_url=self.report_settings.get('REPORT_URL', ''),
        )
        request_data = {'course_ids': self.courses}

        request_data.update(self.get_additional_request_data())

        return request_url, request_data

    def get_report_data(self, report_generation_request_response, request_headers):
        """
        Return the report data according to the API version.

        API v0 does not support pagination so, it will return all response data.
        API v1 supports pagination so, it will request all the pages per course, when there is no more
        pages in any course, it will return all the report data.

        Args:
            report_generation_request_response: Dict containing the report generation response
                                                with the url of the report or the URLs of the pages per course.
            request_headers: Dict that contains the request headers to request the report data.
        Returns:
            report_data: Dict that contains all the report data.
        """
        report_data = {}

        if self.api_version == 'v0':
            report_data = polling_report_data(
                report_data_url=report_generation_request_response.get('state_url', ''),
                request_headers=request_headers,
            )
        elif self.api_version == 'v1':
            response_data = report_generation_request_response.get('data', {})
            report_data = []

            if not response_data:
                print('No response data.')
                exit()

            for course_id in self.courses:
                for page_url in response_data.get(course_id, []):
                    report_data.append(
                        polling_report_data(
                            report_data_url=page_url,
                            request_headers=request_headers,
                        )
                    )

        return report_data

    def init_report_backend(self, report_data):
        """
        Initialize the report backend with the report data and extra data.

        Args:
            report_data: The report data dict object.
        """
        extra_data = self.report_settings.get('EXTRA_DATA', {})
        extra_data['extra_arguments'] = self.command_extra_arguments
        report_builder = self.report_backend(extra_data=extra_data)

        report_builder.generate_report(report_data)

    def get_additional_request_data(self):
        """
        Return extra data to be included in the report request.
        Additional request data must be defined in the report settings in the configuration file,
        within a setting called: EXTRA_REQUEST_DATA.

        You can overwrite any extra request data item from command arguments, to do so
        you only need to add the command argument with the same name that you defined in the
        configuration file and the extra request data item will be overwritten with the command argument value.

        Return:
            request_extra_data: Dict containing the request extra data.
        """
        extra_request_data_from_settings = self.report_settings.get('EXTRA_REQUEST_DATA', {})
        extra_request_data = {}

        for item, value in extra_request_data_from_settings.items():
            extra_request_data[item] = getattr(self.command_extra_arguments, item, value)

        return extra_request_data

    def get_request_headers(self):
        """
        Return a dict containing common request headers.

        Returns:
            Dict that contains common request HTTP headers.
        """
        return {
            'Authorization': 'Bearer {}'.format(self.settings.get('OPEN_EDX_OAUTH_TOKEN', '')),
            'Content-Type': 'application/json',
        }


def polling_report_data(report_data_url, request_headers):
    """
    Polling the report data in some configured unit times.

    Args:
        report_data_url: API url endpoint to request the report data.
        request_headers: Dict that contains the request headers.
    Returns:
        report_data: Report data response.
    """
    polling_count = 0
    report_data = request_handler(
        request_url=report_data_url,
        request_data={},
        request_type='GET',
        request_headers=request_headers,
        query_params={},
    )

    while(report_data.get('status', '') != 'SUCCESS'):
        polling_count += 1
        sleep_for = 2 # every 2 seconds for 10 seconds

        if polling_count >= 5:
            sleep_for = 5 # then every 5 seconds for 20 seconds

        if polling_count >= 9:
            sleep_for = 15 # then every 15 seconds for for a minute

        if polling_count >= 13:
            sleep_for = 60 # then once a minute for 3

        if polling_count >= 16 or report_data.get('status') == 'FAILURE': # then stop
            print('Status failed to become success.')
            print('Failed task URL: {}'.format(report_data_url))
            return {}

        sleep(sleep_for)
        print('waitig for... {}'.format(sleep_for))
        report_data = request_handler(
            request_url=report_data_url,
            request_data={},
            request_type='GET',
            request_headers=request_headers,
            query_params={},
        )

    print('Report data obtained from: {}'.format(report_data_url))
    return report_data


def get_backend_report(report_settings):
    """
    Util function to get the configured report backend from the settings.

    Args:
        report_settings: Dict that contains the report settings.
    """
    backend_module_name = report_settings.get('BACKEND_REPORT', '')

    if not backend_module_name:
        print('BACKEND_REPORT was not provided.')
        exit()

    module_string = backend_module_name.split(':')
    class_string = module_string[-1]
    backend = import_module(module_string[0])

    return getattr(backend, class_string)
