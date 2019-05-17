from .base import AbstractBaseReportBackend
import csv
import os
import boto3
from datetime import datetime
from collections import OrderedDict


class CompletionReportBackend(AbstractBaseReportBackend):
    """
    Backend for Completion report.
    """

    def __init__(self, **kwargs):
        super(CompletionReportBackend, self).__init__(**kwargs)

    def json_report_to_csv(self, json_report_data={}):
        """
        Process json data to convert into csv format.
        """
        report_data = json_report_data.get('result', {})

        if not report_data:
            print('No report data...')
            exit()

        course_list = report_data.keys()

        general_course_data = {}

        for course in course_list:
            course_data = report_data.get(course, [])
            csv_data = []

            for user in course_data:
                username = user.get('username', '')
                user_id = user.get('user_id', '')
                cohort = user.get('cohort', '')
                team = user.get('team', '')
                user_role = user.get('user_role', '')
                vertical_components = user.get('vertical', {})

                vertical = OrderedDict()

                for component in vertical_components:

                    name = '{}-{}'.format(component.get('subsection_name'), component.get('name'))
                    name = self._verify_name(name, vertical)
                    vertical[name] = component.get('complete')

                    unit = general_course_data.get(component.get('number'))

                    if not unit:
                        unit_data = OrderedDict()
                        unit_data['Section Number'] = component.get('section_number')
                        unit_data['Section'] = '{}-{}'.format(component.get('section_number'), component.get('section_name'))
                        unit_data['Subsection Number'] = component.get('subsection_number')
                        unit_data['Subsection'] = '{}-{}'.format(component.get('subsection_number'), component.get('subsection_name'))
                        unit_data['Unit Number'] = component.get('number')
                        unit_data['Unit'] = name
                        unit_data['Complete'] = 1 if component.get('complete') else 0
                        unit_data['Incomplete'] = 0 if component.get('complete') else 1
                        general_course_data[component.get('number')] = unit_data
                    else:
                        unit['Complete'] = 1 + unit['Complete'] if component.get('complete') else unit['Complete']
                        unit['Incomplete'] = unit['Incomplete'] if component.get('complete') else 1 + unit['Incomplete']

                od = OrderedDict()
                od['username'] = username
                od['user_id'] = user_id
                od['cohort'] = cohort
                od['team'] = team
                od['rol'] = user_role
                od.update(vertical)
                csv_data.append(od)

            self.create_csv_file(course, csv_data)
            self.create_csv_file(
                'general_course_data-{}'.format(course),
                [general_course_data[key]for key in general_course_data]
            )

    def create_csv_file(self, course, body_dict):
        """
        Creates the csv file with the passed arguments, and then save it locally.
        """
        path_file = '{parent_folder}/result/{course}.csv'.format(
            parent_folder=os.path.join(os.path.dirname(__file__), os.pardir),
            course=course
        )
        if body_dict:
            with open(path_file, mode='w', encoding='utf-8') as csv_file:
                column_headers = body_dict[0].keys()
                writer = csv.DictWriter(csv_file, fieldnames=column_headers)

                writer.writeheader()
                static_headers = ['user_id', 'username', 'cohort', 'team']

                for row in body_dict:
                    for key, value in row.items():
                        if key not in static_headers:
                            if not value and isinstance(value, bool):
                                row[key] = ''
                            elif isinstance(value, bool):
                                row[key] = 'X'

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
            'cabinet/{course}/completion_report/{date}.csv'.format(
                course=course,
                date=now
            )
        )

    def _verify_name(self, name, data):
        """
        This verifies if the name is already in use and generates a new one.
        """
        if name in data:
            identifier = name.split('-')[-1]
            try:
                number = int(identifier) + 1
                name = name.replace(identifier, str(number))
            except ValueError:
                name = u"{}-{}".format(name, "1")

            name = self._verify_name(name, data)

        return name
