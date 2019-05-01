from .base import AbstractBaseReportBackend
import csv
import os
import boto3
from datetime import datetime


class LastPageAccessedReportBackend(AbstractBaseReportBackend):
    """
    Backend for last time report accessed.
    """

    def __init__(self, **kwargs):
        super(LastPageAccessedReportBackend, self).__init__(**kwargs)


    def json_report_to_csv(self, json_report_data={}):
        """
        Process json data to convert into csv format.
        """
        report_data = json_report_data.get('result', {})

        if not report_data:
            print('No report data...')
            exit()

        course_list = report_data.keys()

        for course in course_list:
            course_data = report_data.get(course, [])
            csv_data = []

            for user in course_data:
                username = user.get('username', '')
                last_time_accessed = user.get('last_time_accessed', '')
                page_url = user.get('page_url', '')

                dict_writer_data = {
                    'username': username,
                    'last_time_accessed': last_time_accessed,
                    'page_url': page_url,
                }
                csv_data.append(dict_writer_data)

            self.create_csv_file(course, csv_data)


    def create_csv_file(self, course, body_dict):
        """
        Creates the csv file with the passed arguments, and then save it locally.
        """
        path_file = '{parent_folder}/result/{course}.csv'.format(
            parent_folder=os.path.join(os.path.dirname(__file__), os.pardir),
            course=course
        )

        with open(path_file, mode='w', encoding='utf-8') as csv_file:
            column_headers = ['username','last_time_accessed', 'page_url']
            writer = csv.DictWriter(csv_file, fieldnames=column_headers)

            writer.writeheader()
            for row in body_dict:
                writer.writerow(row)

        self.upload_file_to_storage(course, path_file)


    def upload_file_to_storage(self, course, path_file):
        """
        Uploads the csv report, to S3 storage.
        """
        amazon_storage = boto3.resource('s3')
        reports_bucket = amazon_storage.Bucket('proversity-custom-reports')
        now = datetime.now()

        reports_bucket.upload_file(
            path_file,
            'cabinet/{course}/last_page_accessed/{date}.csv'.format(
                course=course,
                date=now
            )
        )
