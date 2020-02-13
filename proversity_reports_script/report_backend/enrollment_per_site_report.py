"""
Enrollment per site report backend.
"""
import csv
import os
from collections import OrderedDict
from datetime import datetime, timedelta

import boto3

from proversity_reports_script.google_apis.sheets_api import update_sheets_data
from proversity_reports_script.report_backend.base import AbstractBaseReportBackend


class EnrollmentPerSiteReport(AbstractBaseReportBackend):
    """
    Enrollment per site report class.
    """
    def __init__(self, *args, **kwargs):
        extra_data = kwargs.get('extra_data', {})
        self.bucket_name = extra_data.get('BUCKET_NAME', '')
        self.site_name = getattr(extra_data.get('extra_arguments', {}), 'site_name', '')

        super(EnrollmentPerSiteReport, self).__init__(extra_data.get('SPREADSHEET_DATA', {}))

    def generate_report(self, json_report_data):
        """
        Main logic to generate the report.
        """
        self.json_report_to_csv([data.get('result', {}) for data in json_report_data])

    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.

        Args:
            json_report_data: Dict containing enrollment per site report data.
        """
        if not json_report_data:
            print('No report data...')
            exit()

        report_data = []
        report_data_per_courses = []

        for page_data in json_report_data:
            if not page_data:
                continue

            report_data.extend(build_course_enrollment_per_site_report(page_data))
            row_data = build_courses_per_site_data(page_data)

            # Drop and reduce same course items.
            for index, exisiting_record in enumerate(report_data_per_courses):
                if row_data.get('Course') == exisiting_record.get('Course', ''):
                    try:
                        current = report_data_per_courses.pop(index)
                        current_enrrolled_users = current.get('Number of Enrolled users', 0)
                        row_data_enrolled_users = row_data.get('Number of Enrolled users', 0)

                        row_data.update({
                            'Number of Enrolled users': current_enrrolled_users + row_data_enrolled_users,
                        })
                    except IndexError:
                        pass

            report_data_per_courses.append(row_data)

        self.create_csv_file(
            file_name='enrollment-report',
            body_dict=report_data,
            spreadsheet_range_name='Sheet1',
        )
        self.create_csv_file(
            file_name='enrollment-report-per-courses',
            body_dict=report_data_per_courses,
            spreadsheet_range_name='Sheet2',
        )

    def create_csv_file(self, file_name, body_dict, spreadsheet_range_name):
        """
        Creates the csv file with the passed arguments, and then save it locally.

        Args:
            file_name: File string name.
            body_dict: Dict with the data to write the csv file.
            spreadsheet_range_name: Range name to update the spreadsheet file in A notation:
            https://developers.google.com/sheets/api/guides/concepts#a1_notation
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

        self.upload_file_to_storage(file_path, file_name)
        update_sheets_data(
            file_path,
            self.spreadsheet_data.get('enrollment_per_site', ''),
            spreadsheet_range_name,
        )

    def upload_file_to_storage(self, path_file, file_name_prefix):
        """
        Uploads the csv report, to S3 storage.

        Args:
            path_file: CSV report local file path.
            file_name_prefix: Name prefix of the CSV report file.
        """
        amazon_storage = boto3.resource('s3')
        reports_bucket = amazon_storage.Bucket(self.bucket_name)

        print('S3 Uploading file {} to {}'.format(path_file, self.bucket_name))

        reports_bucket.upload_file(
            path_file,
            'enrollment_per_site_report/{site_name}/{prefix}-{date}.csv'.format(
                site_name=self.site_name,
                prefix=file_name_prefix,
                date=datetime.now(),
            )
        )


def build_course_enrollment_per_site_report(enrollment_data):
    """
    Build and return the enrollment per site data.

    Args:
        enrollment_data: Dict that contains the enrollment per course data.
    Returns:
        report_data: List containing the rows of the report.
    """
    report_data = []
    date_format = '%Y/%m/%d'

    for enrollment in enrollment_data.get('data', []):
        row_data = OrderedDict()
        date_of_registration = get_datetime_object(enrollment.get('date_of_registration', ''))
        date_of_enrollment = get_datetime_object(enrollment.get('date_of_enrollment', ''))
        one_year = timedelta(days=365)

        row_data['Course'] = enrollment_data.get('course', '')
        row_data['Username'] = enrollment.get('username', '')
        row_data['Email'] = enrollment.get('email', '')
        row_data['Role'] = enrollment.get('role', '')
        row_data['Date of Enrollment'] = date_of_enrollment.strftime(date_format)
        row_data['Date of Registration'] = date_of_registration.strftime(date_format)
        row_data['Date of first access'] = date_of_registration.strftime(date_format)
        row_data['Date of Licence Expiration'] = (date_of_registration + one_year).strftime(date_format)
        row_data['Days used'] = (datetime.now() - date_of_registration).days
        row_data['Licence days remaining'] = 365 - (datetime.now() - date_of_registration).days

        report_data.append(row_data)

    return report_data


def get_datetime_object(date_string):
    """
    Return a datetime object according to the date string provided.

    Args:
        date_string: Date string.
    Returns:
        datetime object.
    """
    date = date_string[0:date_string.find(' ')]
    date_object = datetime.strptime(date, '%Y-%m-%d')

    return date_object


def build_courses_per_site_data(enrollment_data):
    """
    Return the enrollment and registered users per course.

    Args:
        enrollment_data: Dict that contains the enrollment per course data.
    Returns:
        row_data: Course row data.
    """
    row_data = OrderedDict()
    row_data['Course'] = enrollment_data.get('course', '')
    row_data['Number of Registered users'] = enrollment_data.get('registered_users', 0)
    row_data['Number of Enrolled users'] = len(enrollment_data.get('data', []))

    return row_data
