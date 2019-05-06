"""
Last page accessed reports backend.
"""
import csv
from datetime import datetime
import os

import boto3


from .base import AbstractBaseReportBackend


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

        if report_data.get('last_page_data'):
            last_page_data = report_data.get('last_page_data')
            for course in last_page_data.keys():
                last_page_report = self.last_page_accessed_report(course, last_page_data)
                last_page_report_headers = ['username', 'last_time_accessed', 'last_page_viewed']
                file_name = '{}-table'.format(course)

                self.create_csv_file(file_name, last_page_report, last_page_report_headers)

        if report_data.get('exit_count_data'):
            exit_count_data = report_data.get('exit_count_data')
            for course in last_page_data.keys():
                exit_count_report = self.exit_count_report(course, exit_count_data)
                exit_count_report_headers = ['page_title', 'exit_count',]
                file_name = '{}-bar-chart'.format(course)

                self.create_csv_file(file_name, exit_count_report, exit_count_report_headers)


    def create_csv_file(self, file_name, body_dict, headers):
        """
        Creates the csv file with the passed arguments, and then save it locally.
        """
        path_file = '{parent_folder}/result/{file_name}.csv'.format(
            parent_folder=os.path.join(os.path.dirname(__file__), os.pardir),
            file_name=file_name
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


    def last_page_accessed_report(self, course, last_page_data):
        """
        Returns a csv dict to write the csv file.
        """
        if not last_page_data:
            return {}

        course_data = last_page_data.get(course, [])
        csv_data = []

        for user in course_data:
            username = user.get('username', '')
            last_time_accessed = user.get('last_time_accessed', '')
            last_page_viewed = user.get('last_page_viewed', '')

            dict_writer_data = {
                'username': username,
                'last_time_accessed': last_time_accessed,
                'last_page_viewed': last_page_viewed,
            }
            csv_data.append(dict_writer_data)

        return csv_data


    def exit_count_report(self, course, exit_count_data):
        """
        Returns a csv dict to write the csv file.
        """
        if not exit_count_data:
            return {}

        course_data = exit_count_data.get(course, [])
        csv_data = []

        for block in course_data:
            page_title = block.get('page_title', '')
            exit_count = block.get('exit_count', '')

            dict_writer_data = {
                'page_title': page_title,
                'exit_count': exit_count,
            }
            csv_data.append(dict_writer_data)

        return csv_data
