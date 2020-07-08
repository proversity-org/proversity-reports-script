"""
Module containing common functions for requesting API V1 reports.
"""
from proversity_reports_script.request_module import request_handler


def get_report_generation_data(*args, **kwargs):
    """
    Return the data from the generation report request.

    For API v1, to avoid requesting data for a large set of courses (and probably get a 504 error),
    the report generation request is divided into groups of courses
    determined by EXTRA_DATA['MAX_COURSES_PER_REQUEST'] from the report configuration.
    Each response data is collected into one object.

    Keyword args:
        request_data: Dict containing the complete list of courses and other information.
        request_url: Request API URL.
        report_settings: Dict containing the report settings from the config file.
        request_headers: Dict containing some HTTP request headers to perform the request.
        extra_request_data: Dict containing some additional data to add to the request.
    Returns:
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
    report_generation_request_data = kwargs.get('request_data', {})
    initial_report_request_url = kwargs.get('request_url', '')
    report_generation_data = {}
    course_groups = get_course_groups(
        courses=report_generation_request_data.get('course_ids', []),
        max_courses_per_request=kwargs.get(
            'report_settings', {},
        ).get('EXTRA_DATA', {}).get('MAX_COURSES_PER_REQUEST', 10),
    )

    for course_group in course_groups:
        report_generation_request_data.update({
            'course_ids': course_group,
        })

        existing_report_data = report_generation_data.get('data', {})

        print('Report generation requested to: {}'.format(initial_report_request_url))

        response_data = request_handler(
            request_url=initial_report_request_url,
            request_data=report_generation_request_data,
            request_type='POST',
            request_headers=kwargs.get('request_headers', {}),
            query_params=kwargs.get('extra_request_data', {}).get('query_params', {}),
        )

        existing_report_data.update(response_data.get('data', {}))
        report_generation_data.update({
            'data': existing_report_data,
        })

    return report_generation_data


def get_course_groups(courses, max_courses_per_request):
    """
    Return a list of course lists
    in groups determined by max_courses_per_request value.

    Args:
        courses: Complete list of courses.
        max_courses_per_request: Maximum number of courses per group.
    Returns:
        List of list:
            [
                ['course one', 'course two', 'course three', 'course four'],
                ['course one', ...], ...
            ]
    """
    course_groups = []

    for cursor_index in range(0, len(courses), max_courses_per_request):
        course_groups.append(courses[cursor_index:cursor_index + max_courses_per_request])

    return course_groups
