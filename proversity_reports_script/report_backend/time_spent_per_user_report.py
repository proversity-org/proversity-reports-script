"""
Time spent per user report backend.
"""
import csv
import functools
import os
from datetime import datetime

import boto3

from proversity_reports_script.google_apis.sheets_api import update_sheets_data
from proversity_reports_script.report_backend.base import AbstractBaseReportBackend


class TimeSpentPerUserReportBackend(AbstractBaseReportBackend):
    """
    Backend for time spent per user report.
    """

    def __init__(self, *args, **kwargs):
        extra_data = kwargs.get('extra_data', {})
        self.bucket_name = extra_data.get('BUCKET_NAME', '')

        super(TimeSpentPerUserReportBackend, self).__init__(extra_data.get('SPREADSHEET_DATA', {}))

    def generate_report(self, json_report_data):
        """
        Main logic to generate the report.
        """
        self.json_report_to_csv(json_report_data)

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

        for course_key, course_data in report_data.items():
            file_name = '{}'.format(course_key)

            if not course_data:
                continue

            time_spent_per_user_report_data = build_time_spent_report_data(course_data)

            self.create_csv_file(
                file_name=file_name,
                body_dict=time_spent_per_user_report_data,
                course_id=course_key,
                spreadsheet_range_name='Sheet1',
            )

            time_spent_per_team_report_data = grouping_report_data_by_key(course_data, 'user_teams')

            self.create_csv_file(
                file_name='{}-teams'.format(file_name),
                body_dict=time_spent_per_team_report_data,
                course_id=course_key,
                spreadsheet_range_name='Sheet2',
                file_name_prefix='teams-',
            )

            time_spent_per_cohort_report_data = grouping_report_data_by_key(course_data, 'user_cohort')

            self.create_csv_file(
                file_name='{}-cohorts'.format(file_name),
                body_dict=time_spent_per_cohort_report_data,
                course_id=course_key,
                spreadsheet_range_name='Sheet3',
                file_name_prefix='cohorts-',
            )

    def create_csv_file(self, file_name, body_dict, course_id, spreadsheet_range_name, file_name_prefix=''):
        """
        Creates the csv file with the passed arguments, and then save it locally.

        Args:
            file_name: File string name.
            body_dict: Dict with the data to write the csv file.
            course_id: Course key value.
            spreadsheet_range_name: Range name to update the spreadsheet file in A notation:
            https://developers.google.com/sheets/api/guides/concepts#a1_notation
            file_name_prefix: Prefix of the file to upload to Amazon S3.
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

        self.upload_file_to_storage(course_id, file_path, file_name_prefix)
        update_sheets_data(
            file_path,
            self.spreadsheet_data.get('time_spent_sheet_id_{}'.format(course_id)),
            spreadsheet_range_name,
        )

    def upload_file_to_storage(self, course, path_file, file_name_prefix):
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
            'cabinet/{course}/time_spent_per_user_report/{prefix}{date}.csv'.format(
                course=course,
                prefix=file_name_prefix,
                date=now,
            )
        )


def build_time_spent_report_data(course_data):
    """
    Returns a dict containing the essential data to generate the time spent csv report.

    Args:
        course_data: List with the course structure by subsection data.
    Returns:
        List containing the data to generate the report.
        [{
            section: Course section string name.
            subsection: Course subsection string name.
            page_views: Total of subsection views.
            time_on_page: Total of the average time on page.
        }]
    """
    report_course_data = []

    for user_data in course_data:
        course_blocks = user_data.get('blocks', [])
        user_report_data = {
            'Student': user_data.get('username', ''),
            'Cohort': user_data.get('user_cohort', ''),
            'Teams': user_data.get('user_teams', ''),
        }

        for course_block_index, course_block in enumerate(course_blocks):
            vertical_name = course_block.get('vertical_name', '')

            if vertical_name in user_report_data.keys():
                vertical_name = '{}-{}'.format(vertical_name, course_block_index)

            user_report_data.update({
                vertical_name: course_block.get('average_time_spent', 0),
            })

        report_course_data.append(user_report_data)

    return report_course_data


def grouping_report_data_by_key(course_data, grouping_key):
    """
    Groups the report data by the key provided (user_cohort/user_teams)
    to obtain the total time spent by all the team/cohort members in each unit.

    Args:
        course_data: List with the course structure by unit data.
        grouping_key: Name of the key to group the data.
    Returns:
        List containing the data to generate the report.
        [{
            section_position: Chapter position in the course structure.
            section: Course chapter string name.
            subsection_position: Subsection position in the course structure.
            subsection: Course subsection string name.
            vertical_position: Unit position in the course structure.
            vertical_name: Course unit string name.
            group/cohort name: Value of the time spent by team/cohort members in seconds.
            ...
        }]
    """
    course_groups = set([data.get(grouping_key, '') for data in course_data])
    group_report_data = []

    for group in course_groups:
        block_groups = []

        # Group identical blocks of the users in the same group.
        # [
        #   ({'block': 'A-block'},{'block': 'A-block'},{'block': 'A-block'}),
        #   ({'block': 'B-block'},{'block': 'B-block'},{'block': 'B-block'}),
        #   ...
        # ]
        for user in course_data:
            if user.get(grouping_key, '') == group:
                for index, course_block in enumerate(user.get('blocks', [])):
                    try:
                        current = block_groups.pop(index)
                    except IndexError:
                        current = ()

                    block_groups.insert(index, current + (course_block, ))

        # Reduce the identical blocks to only one block.
        for block_group_index, block_group in enumerate(block_groups):
            course_teams_dict = {course_team: 0 for course_team in course_groups}

            try:
                current_block = block_group[0]
            except IndexError:
                continue

            block_data = {
                'section_position': current_block.get('chapter_position', ''),
                'section': current_block.get('chapter_name', ''),
                'subsection_position': current_block.get('sequential_position', ''),
                'subsection': current_block.get('sequential_name', ''),
                'vertical_position': current_block.get('vertical_position', ''),
                'vertical_name': current_block.get('vertical_name', ''),
            }

            # Sum all the average_time_spent.
            course_teams_dict[group] = functools.reduce(
                lambda x, y: x + y,
                [average.get('average_time_spent', 0) for average in block_group],
            )

            block_data.update(course_teams_dict)

            # Reduce the course structure to only one structure with the total time spent by team/cohort members.
            try:
                current = group_report_data.pop(block_group_index)

                for group_value in course_groups:
                    block_data[group_value] += current.get(group_value, 0)
            except IndexError:
                pass

            group_report_data.insert(block_group_index, block_data)

    return group_report_data
