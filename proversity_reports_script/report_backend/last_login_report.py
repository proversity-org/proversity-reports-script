"""
Last login report backend.
"""
import csv
import os
from collections import OrderedDict
from datetime import datetime

import boto3

from proversity_reports_script.google_apis.sheets_api import update_sheets_data
from proversity_reports_script.report_backend.base import AbstractBaseReportBackend


class LastLoginReportBackend(AbstractBaseReportBackend):
    """
    Backend for last login report.
    """

    def __init__(self, *args, **kwargs):
        extra_data = kwargs.get('extra_data', {})
        self.bucket_name = extra_data.get('BUCKET_NAME', '')
        self.spreadsheet_range = extra_data.get('SPREADSHEET_RANGE_NAME', 'Sheet1')

        super(LastLoginReportBackend, self).__init__(extra_data.get('SPREADSHEET_DATA', {}))

    def generate_report(self, json_report_data):
        """
        Main logic to generate the report.
        """
        self.json_report_to_csv(json_report_data.get('result', {}))

    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.

        Args:
            json_report_data: Json representacion containing last login report data.
        """
        if not json_report_data:
            print('No report data...')
            exit()

        for course_id, course_data in json_report_data.items():
            self.create_csv_file(
                file_name=course_id,
                body_dict=build_csv_rows_data(course_data),
                course_id=course_id,
            )

    def create_csv_file(self, file_name, body_dict, course_id):
        """
        Creates the csv file with the passed arguments, and then save it locally.

        Args:
            file_name: File string name.
            body_dict: Dict with the data to write the csv file.
            course_id: Course key value.
        """
        file_path = '{parent_folder}/result/{file_name}.csv'.format(
            parent_folder=os.path.join(os.path.dirname(__file__), os.pardir),
            file_name=file_name,
        )

        try:
            headers = body_dict[0].keys()
        except IndexError:
            return None

        with open(file_path, mode='w', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)

            writer.writeheader()

            for row in body_dict:
                writer.writerow(row)

        self.upload_file_to_storage(course_id, file_path)
        update_sheets_data(
            file_path=file_path,
            spreadsheet_id=self.spreadsheet_data.get('last_login_report_{}'.format(course_id)),
            spreadsheet_range_name=self.spreadsheet_range,
        )

    def upload_file_to_storage(self, course, path_file):
        """
        Uploads the csv report, to S3 storage.

        Args:
            course: Course string id.
            path_file: CSV report local file path.
        """
        amazon_storage = boto3.resource('s3')
        reports_bucket = amazon_storage.Bucket(self.bucket_name)
        now = datetime.now()

        print('S3 Uploading file {} to {}'.format(path_file, self.bucket_name))

        reports_bucket.upload_file(
            path_file,
            'reports/{course}/last_login_report/{date}.csv'.format(
                course=course,
                date=now,
            )
        )


def build_csv_rows_data(course_data):
    """
    Create the dict to write the CSV file.

    Args:
        course_data: Dict that contains the course report data.
    Returns:
        report_data: List that contains the rows to write the CSV file.
    """
    report_data = []

    for user_data in course_data:
        user_report_data = OrderedDict()
        user_report_data['Username'] = user_data.get('username', '')
        user_report_data['Email'] = user_data.get('email', '')
        user_report_data['Last login to the platform'] = user_data.get('last_login_date', '')
        user_report_data['Date of registration'] = user_data.get('date_of_registration', '')

        report_data.append(user_report_data)

    return report_data
