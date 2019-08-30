"""
Acitivity completion report backend.
"""
import csv
import os
from datetime import datetime

import boto3

from proversity_reports_script.report_backend.base import AbstractBaseReportBackend


class ActivityCompletionReportBackend(AbstractBaseReportBackend):
    """
    Backend for activity completion report.
    """

    def __init__(self, *args, **kwargs):
        extra_data = kwargs.get('extra_data', {})
        self.bucket_name = extra_data.get('BUCKET_NAME', '')

        super(ActivityCompletionReportBackend, self).__init__(extra_data.get('SPREADSHEET_DATA', {}))


    def generate_report(self, json_report_data):
        """
        Main logic to generate the report.
        """
        self.json_report_to_csv(json_report_data)


    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.
        """
        for course, course_data in iter(json_report_data.get('result', {}).items()):
            csv_data = generate_csv_dict(course_data)

            if not csv_data:
                continue

            self.create_csv_file(
                course,
                csv_data,
                csv_data[0].keys(),
            )


    def create_csv_file(self, file_name, body_dict, headers, *args, **kwargs):
        """
        Create the csv file with the passed arguments, and then save it locally.
        """
        path_file = '{parent_folder}/result/{file_name}.csv'.format(
            parent_folder=os.path.join(os.path.dirname(__file__), os.pardir),
            file_name=file_name,
        )

        with open(path_file, mode='w', encoding='utf-8') as csv_file:
            column_headers = headers
            writer = csv.DictWriter(csv_file, fieldnames=column_headers)

            writer.writeheader()

            for row in body_dict:
                writer.writerow(row)

        self.upload_file_to_storage(file_name, path_file)


    def upload_file_to_storage(self, course, path_file):
        """
        Upload the csv report, to S3 storage.
        """
        amazon_storage = boto3.resource('s3')
        reports_bucket = amazon_storage.Bucket(self.bucket_name)
        now = datetime.now()

        reports_bucket.upload_file(
            path_file,
            'reports/{course}/activity_completion_report/{date}.csv'.format(
                course=course,
                date=now,
            )
        )


def generate_csv_dict(course_data={}):  # pylint: disable=dangerous-default-value
    """
    Return a csv dict to write the csv file.
    """
    csv_data = []

    for user_data in course_data:
        email = user_data.get('email', '')
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')

        dict_writer_data = {}

        dict_writer_data['First Name'] = first_name
        dict_writer_data['Last Name'] = last_name
        dict_writer_data['Email'] = email

        dict_writer_data.update(get_required_activity_dict(user_data))

        csv_data.append(dict_writer_data)

    return csv_data


def get_required_activity_dict(user_data):
    """
    Create a dict with the required activity data.

    Args:
        user_data: Report json data per course.
    Returns:
        Dict containing activities info.
        {
            'Multiple Choice': 'completed',
            'Image Explorer': 'completed',
            'Video': 'not_completed'
        }
    """
    required_activities_data = {}
    total_activities = user_data.get('total_activities', 0)

    if total_activities:
        total = int(total_activities)
        # Create as many 'required_activity_' as the total number of activities.
        for activity_number in range(1, total + 1): # Plus 1, because the stop argument it's not inclusive.
            required_activity_number = user_data.get('required_activity_{}'.format(activity_number), '')
            required_activity_name = user_data.get('required_activity_{}_name'.format(activity_number), '')

            # Let's add the activity number at the end of the name if two or more activities have the same name.
            if required_activity_name in required_activities_data.keys():
                required_activity_name = '{}-{}'.format(
                    required_activity_name,
                    activity_number,
                )

            required_activities_data.update({
                required_activity_name: required_activity_number,
            })

    return required_activities_data
