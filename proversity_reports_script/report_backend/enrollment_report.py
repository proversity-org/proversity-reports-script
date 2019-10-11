"""
Report backend for enrollment report.
"""
import csv
import json
import os

import boto3
import requests

from proversity_reports_script.get_settings import get_settings
from proversity_reports_script.report_backend.base import AbstractBaseReportBackend

BATCH_SIZE = 15
DEFAULT_LEAD_SOURCE = 'Salesforce'
COURSES_DETAILS_FILE_PATH='PearsonX-Program-Structure .csv'


class EnrollmentReportBackend(AbstractBaseReportBackend):
    """
    Backend for enrollment report.
    """

    def __init__(self, *args, **kwargs):
        self.extra_data = kwargs.get('extra_data', {})
        self.settings = get_settings(False)

    def generate_report(self, json_report_data):
        """
        Main logic to generate the enrollment report.

        First, gets the enrollemnt data from the platform,
        Then, attempts to create the enrollments wihtout contact id into Salesforce,
        Then, when the contact id is returned from Salesforce
        attempts to create the contact id record in the platform.
        """
        print('Processing enrollment report...')

        for course, course_data in iter(json_report_data.get('result', {}).items()):
            salesforce_data = self._get_salesforce_data(course, course_data)
            salesforce_result = self._create_saleforce_enrollments(salesforce_data)
            self._create_platform_users_contact_id(salesforce_result)

    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.
        """
        pass

    def create_csv_file(self, file_name, body_dict, headers, spreadsheet_id):
        """
        Creates the csv file with the passed arguments, and then save it locally.
        """
        pass

    def upload_file_to_storage(self, course, path_file):
        """
        Uploads the csv report, to the implemented storage.
        """
        pass

    def _get_salesforce_data(self, course, course_data):
        """
        Returns the Salesforce data according to the API specification.

        A list of lists will be returned
        and the size of the items in the list will be calculated from the BATCH_SIZE number.

        Args:
            course: course id string.
            course_data: The enrollment report data returned from the platform.
        Returns:
            salesforce_data: List of lists with a size predifined by the BATCH_SIZE number.
        """
        def get_first_and_last_name(full_name):
            """
            Takes the argument full_name and returns the first name and last name separately.
            If the full name value cannot be splitted at least once, it will return
            the full_name argument as name and last name.

            Args:
                full_name: The student full name.
            Returns:
                name: The name of the student.
                last_name: The last name of the student.
            """
            result = full_name.split(' ', 1)

            if len(result) == 2:
                return result

            return full_name, full_name

        def get_course_info_from_file(course_key):
            """
            Get course details from S3 file
            """
            course_details = {}
            s3 = boto3.resource('s3')
            bucket = s3.Bucket('pearson-prod')

            # download file
            with open('courses.csv', 'wb') as data:
                bucket.download_fileobj(COURSES_DETAILS_FILE_PATH, data)

            # reading file
            with open('courses.csv', 'r') as csv_data:
                reader = csv.DictReader(csv_data)
                for row in reader:
                    if row['Course key'] == course_key:
                        course_details['program'] = row['Program of Interest - EO']
                        course_details['company'] = row['Company / Account']
                        course_details['type'] = row['Type Hidden']
                        course_details['institution'] = row['Instutition Hidden']
                        break

            # cleaning
            if os.path.exists('courses.csv'):
                os.remove('courses.csv')

            return course_details

        salesforce_data = []
        batch = []
        course_details = get_course_info_from_file(course)

        for index, user in enumerate(course_data, 1):
            contact_id = user.get('contact_id', '')

            # If the user doesn't have a user_id, the creation cannot be possible.
            if not user.get('user_id', ''):
                continue

            # If the user has already a contact id,
            # it's not neccesary to request the creation again.
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
                'LastName': last_name if last_name else username,
                'Email': user.get('email', ''),
                'Company': course_details.get('company', ''),
                'Institution_Hidden': course_details.get('institution', ''),
                'Type_Hidden': course_details.get('type', ''),
                'Program_of_Interest': course_details.get('program', ''),
                'Intake_of_Intent': user.get('intake_of_intent', ''),
                'Lead_Source': self.extra_data.get('LEAD_SOURCE', DEFAULT_LEAD_SOURCE),
                'Program_Code': course,
                'Drupal_ID': user.get('user_id', ''),
            }

            batch.append(user_salesforce_data)

            if len(batch) == BATCH_SIZE or index == len(course_data):
                salesforce_data.append(batch)
                batch = []

        return salesforce_data

    def _create_saleforce_enrollments(self, enrollment_data):
        """
        Creates the enrollment list into Salesforce.

        Args:
            enrollment_data: List of list with the enrollment data.
        Returns:
            salesforce_result: List wiht the contact id data from Salesforce.
        """
        request_session = requests.Session()
        salesforce_details = self._get_salesforce_details()
        enrollment_api_url = self.extra_data.get('SALESFORCE', {}).get(
            'SALESFORCE_API_ENROLLMENT_URL',
            ''
        )

        if not enrollment_api_url:
            print('SALESFORCE_API_ENROLLMENT_URL was not provided.')
            exit()

        api_url = '{}{}'.format(
            salesforce_details.get('instance_url', ''),
            enrollment_api_url,
        )

        request_session.headers.update({
            'Authorization': '{} {}'.format(
                salesforce_details.get('token_type', ''),
                salesforce_details.get('access_token', ''),
            ),
        })

        print('Creating enrollments on Salesforce...')

        salesforce_result = []

        for enrollments in enrollment_data:
            request_data = {
                'enrollments': enrollments,
            }

            api_response = request_session.post(api_url, json=request_data)

            if api_response.ok:
                salesforce_result.append(api_response.json())
            else:
                print('There was an error calling the Salesforce API: ', api_response.text)

        return salesforce_result

    def _get_salesforce_details(self):
        """
        Returns the Salesforce details from the authentication request.

        Returns:
            A dict with some Salesforce deatils.
            {
                'access_token': Salesforce access token.
                'instance_url': Salesforce instance url.
                'token_type': Access token type.
            }
        """
        print('Getting Salesforce token deatils...')

        salesforce_data = self.extra_data.get('SALESFORCE', {})

        if not salesforce_data:
            print('SALESFORCE data was not provided.')
            exit()

        salesforce_url = salesforce_data.get('AUTHENTICATION_URL', '')

        if not salesforce_url:
            print('Salesforce AUTHENTICATION_URL was not provided.')
            exit()

        request_data = {
            'grant_type': 'password',
            'client_id': salesforce_data.get('CLIENT_ID', ''),
            'username': salesforce_data.get('USERNAME', ''),
            'client_secret': salesforce_data.get('CLIENT_SECRET', ''),
            'password': '{}{}'.format(
                salesforce_data.get('PASSWORD', ''),
                salesforce_data.get('SECURITY_TOKEN', ''),
            ),
        }

        request_response = requests.post(salesforce_url, data=request_data)

        if not request_response.ok:
            print('Salesforce authentication failure, reason:', request_response.text)
            exit()

        response_data = request_response.json()

        return {
            'access_token': response_data.get('access_token'),
            'instance_url': response_data.get('instance_url', ''),
            'token_type': response_data.get('token_type', ''),
        }

    def _create_platform_users_contact_id(self, users_data):
        """
        Creates the contact id record on the platform side.

        Args:
            users_data: Enrollment data returned from Salesforce.
        """
        def process_user_data(users_data):
            """
            Creates a new dict from the Salesforce enrollment data in order to
            fits with the SalesforceContactId model of the platform.

            Args:
                users_data: Dict with the Salesforce enrollemnt data.
            Returns:
                final_user_data: Dict containing the user_id and the contact_id values.
            """
            final_user_data = []

            for user_data in users_data:
                final_user_data.append({
                    'user_id': user_data.get('DrupalID', ''),
                    'contact_id': user_data.get('ContactID', ''),
                })

            return final_user_data

        print('Creating records in the platform...')

        request_session = requests.Session()
        contact_id_api_url = self.extra_data.get('CONTACT_ID_API_URL', '')

        if not contact_id_api_url:
            print('CONTACT_ID_API_URL was not provided.')
            exit()

        api_url = '{}{}'.format(
            self.settings.get('LMS_URL', ''),
            contact_id_api_url,
        )

        request_session.headers.update({
            'Authorization': 'Bearer {}'.format(self.settings.get('OPEN_EDX_OAUTH_TOKEN', '')),
        })

        for data in users_data:
            request_data = {
                'records': process_user_data(data),
            }

            response = request_session.post(api_url, json=request_data)

            if not response.ok:
                print('There was an error calling the Platform API: ', response.text)
