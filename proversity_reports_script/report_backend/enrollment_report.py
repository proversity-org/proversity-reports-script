"""
Report backend for enrollment report.
"""
import six

import requests

from proversity_reports_script.report_backend.base import AbstractBaseReportBackend

BATCH_SIZE = 15


class EnrollmentReportBackend(AbstractBaseReportBackend):
    """
    Backend for enrollment report.
    """

    def __init__(self, *args, **kwargs):
        self.extra_data = kwargs.get('extra_data', {})

    def generate_report(self, json_report_data):
        """
        Main logic to generate the report.
        """
        for course, course_data in six.iteritems(json_report_data.get('result', [])):
            salesforce_data = self._get_salesforce_data(course, course_data)
            salesforce_result = self._update_saleforce_enrollments(salesforce_data)
            self._update_platform_users(salesforce_result)

    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.
        """
        raise NotImplementedError()

    def create_csv_file(self, course, body_dict, spreadsheet_id):
        """
        Creates the csv file with the passed arguments, and then save it locally.
        """
        raise NotImplementedError()

    def upload_file_to_storage(self, course, path_file):
        """
        Uploads the csv report, to S3 storage.
        """
        raise NotImplementedError()

    def _get_salesforce_data(self, course, course_data):
        """
        """
        def get_first_and_last_name(full_name):
            """
            Takes the argument full_name a returns a list with the first name and last name
            """
            try:
                result = full_name.split(' ', 1)
            except AttributeError:
                return '', ''
            else:
                if len(result) == 2:
                    return result
                return full_name, full_name

        salesforce_data = []
        batch = []
        for index, user in enumerate(course_data, 1):

            contact_id = user.get('contact_id')

            if contact_id and index == len(course_data):
                salesforce_data.append(batch)
                batch = []
                continue
            elif contact_id:
                continue

            first_name, last_name = get_first_and_last_name(user.get('full_name', ''))
            username = user.get('username', '')

            user_salesforce_data = {
                'FirstName': first_name if first_name else username,
                'LastName': last_name if last_name else '',
                'Email': user.get('email'),
                'Company': 'TNE',
                'Institution_Hidden': 'TNE-IN-PPP',
                'Type_Hidden': 'TNE',
                'Program_of_Interest': 'ITPR-IN Shiny R',
                'Intake_of_Intent': 'September 2019',
                'Lead_Source': 'Facebook',
                'Secondary_Source': 'Test',
                'Tertiary_Source': 'OpenEdX',
                'Program_Code': course,
                'Drupal_ID': user.get('user_id')
            }
            batch.append(user_salesforce_data)

            if len(batch) == BATCH_SIZE or index == len(course_data):
                salesforce_data.append(batch)
                batch = []

        return salesforce_data

    def _update_saleforce_enrollments(self, data):
        """
        """
        session = requests.Session()
        session.headers.update(self._get_salesforce_headers())
        url = self.extra_data.get('SALESFORCE', {}).get('URL_OPEN_EDX_API')

        if not url:
            print('URL_OPEN_EDX_API was not provided.')
            exit()

        salesforce_result = []

        for enrollments in data:
            response = session.post(url, data={'enrollments': enrollments})

            if response.ok:
                salesforce_result.append(response.json())

        return salesforce_result

    def _get_salesforce_headers(self):
        """
        """
        salesforce_data = self.extra_data.get('SALESFORCE')

        if not salesforce_data:
            print('Salesforce data was not provided.')
            exit()

        salesforce_url = salesforce_data.get('AUTHENTICATION_URL')

        data = {
            'grant_type': 'password',
            'client_id': salesforce_data.get('CLIENT_ID'),
            'username': salesforce_data.get('USERNAME'),
            'client_secret': salesforce_data.get('CLIENT_SECRET'),
            'password': '{}{}'.format(salesforce_data.get('PASSWORD'), salesforce_data.get('SECURITY_TOKEN'))
        }

        response = requests.post(salesforce_url, data=data)

        if response.ok:
            response_data = response.json()

            return {
                'Authorization': '{} {}'.format(response_data.get('token_type'), response_data.get('access_token'))
            }

        print('Salesforce authentication failure, reason =', response.text)
        exit()

    def _update_platform_users(self, users_data):
        """
        """
        session = requests.Session()
        session.headers.update({
            'Authorization': 'Bearer {}'.format(self.extra_data.get('OPEN_EDX_OAUTH_TOKEN')),
            'Content-Type': 'application/json',
        })
        url = self.extra_data.get('STUDENT_ACCOUNT_API_URL', {})

        if not url:
            print('STUDENT_ACCOUNT_API_URL was not provided.')
            exit()

        for data in users_data:
            response = session.post(url, data=data)

            if not response.ok:
                print(response.text)
