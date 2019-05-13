"""
Time spent report backend.
"""
import csv
from datetime import datetime
import os

import boto3


from .base import AbstractBaseReportBackend


class TimeSpentReportBackend(AbstractBaseReportBackend):
    """
    Backend for time spent report.
    """

    def __init__(self, **kwargs):
        super(TimeSpentReportBackend, self).__init__(**kwargs)


    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.

        Args:
            json_report_data: Json representacion containing time spent report data.
        """
        report_data = json_report_data.get('result', {})

        if not report_data:
            print('No report data...')
            exit()

        if report_data.get('time_spent_data'):
            time_spent_data = report_data.get('time_spent_data', {})
            for course_key, course_data in time_spent_data.items():
                file_name = '{}'.format(course_key)

                if not course_data:
                    continue

                analytics_data = course_data.get('analytics_data', [])
                course_structure_data = course_data.get('course_structure', [])

                subsection_data = count_analytics_subsections(analytics_data, course_structure_data)
                report_csv_headers = [
                    'section_position',
                    'section',
                    'subsection_position',
                    'subsection',
                    'page_views',
                    'time_on_page'
                ]

                self.create_csv_file(file_name, subsection_data, report_csv_headers)


    def create_csv_file(self, file_name, body_dict, headers):
        """
        Creates the csv file with the passed arguments, and then save it locally.

        Args:
            file_name: File string name.
            body_dict: Dict with the data to write the csv file.
            headers: List with the csv column names.
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

        Args:
            course: Course string id.
            path_file: CSV report local file path.
        """
        amazon_storage = boto3.resource('s3')
        reports_bucket = amazon_storage.Bucket('proversity-custom-reports')
        now = datetime.now()

        reports_bucket.upload_file(
            path_file,
            'cabinet/{course}/time_spent_report/{date}.csv'.format(
                course=course,
                date=now
            )
        )


def count_analytics_subsections(analytics_data, course_structure_data):
    """
    Returns a dict containing the essential data to generate the time spent csv report.

    Args:
        analytics_data: List with the Google Analytics data.
        course_structure_data: List with the course structure by subsection data.
    Returns:
        List containing the data to generate the report.
        [{
            section: Course section string name.
            subsection: Course subsection string name.
            page_views: Total of subsection views.
            time_on_page: Total of the average time on page.
        }]
    """
    subsection_data = []

    for course_block in course_structure_data:
        sequential_id = course_block.get('sequential_id', '')
        subsections_occurrences = [
            item for item in analytics_data if sequential_id in item.get('page_path')
        ]
        total_page_views = 0
        total_time_on_page = 0

        for analytics_item in subsections_occurrences:
            total_page_views += int(analytics_item.get('page_views', 0))
            total_time_on_page += float(analytics_item.get('avg_time_on_page', 0))

        subsection_data.append({
            'section_position': course_block.get('chapter_position', ''),
            'section': course_block.get('chapter_name', ''),
            'subsection_position': course_block.get('sequential_position', ''),
            'subsection': course_block.get('sequential_name', ''),
            'page_views': total_page_views,
            'time_on_page': total_time_on_page,
        })

    return subsection_data
