"""
Helper module with utilities to generate the content of a message.
"""
import csv
import base64
import os

import boto3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')
import seaborn as sns
sns.set()


def generate_graph(**kwargs):
    """
    Helper method to generate a graph from its subplots.
    """

    if not kwargs.get("subplots"):
        return None

    try:
        script_dir = os.path.dirname(__file__)
        rel_path = "output.png"
        fig, axes = plt.subplots(
            nrows=1,
            ncols=len(kwargs["subplots"]),
            figsize=(10.0, 5.0)
        )
        fig.subplots_adjust(hspace=0.5)

        for idx, subplot in enumerate(kwargs["subplots"]):
            sns.barplot(
                x=subplot["x"],
                y=subplot["y"],
                data=subplot["data"],
                ax=axes[idx],
                palette=subplot["palette"],
            )
            axes[idx].set_xlabel('')
            axes[idx].title.set_text(subplot["title"])
            axes[idx].set_ylabel(subplot["ylabel"])

        fig.tight_layout()
        fig.savefig(os.path.join(script_dir, rel_path))
    except Exception:
        return None
    else:
        return "Completed"


def generate_student_subplots(user_record, graph_confs):
    """
    Generate a subplots data for the main graph.
    """

    subplots_data = []

    for key, graph in graph_confs.items():
        try:
            subplots_data.append({
                "x": "metric_category",
                "y": key,
                "data": pd.DataFrame({
                    key: [
                        graph["passing_score"],
                        user_record[key]
                    ],
                    "metric_category": ["Target", "You"]
                }),
                "ylabel": graph["ylabel"],
                "title": graph["graph_title"],
                "palette": "Blues_d",
            })
        except Exception:
            return None

    return subplots_data


def get_graph():
    """
    Get the image from the folder and return its string representation.
    """
    encoded_string = None
    try:
        script_dir = os.path.dirname(__file__)
        rel_path = "output.png"
        abs_file_path = os.path.join(script_dir, rel_path)
        with open(abs_file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        if os.path.exists(abs_file_path):
            os.remove(abs_file_path)
    except Exception as identifier:
        return None
    else:
        return encoded_string



# testing methods
def get_course_info_from_file(course_key, week):
    """
    Get course details from S3 file
    """
    threshold = {}
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('pearson-prod')

    # download file
    with open('ltr-metrics.csv', 'wb') as data:
        temp = 'PX-Courses-Info.csv'
        bucket.download_fileobj(temp, data)

    # reading file
    with open('ltr-metrics.csv', 'r') as csv_data:
        reader = csv.DictReader(csv_data)
        for row in reader:
            # set required look up
            conditions = [
                row['Course key'] == course_key,
                row['Week'] == course_key,
                row['Course key'] == course_key,
            ]
            if row['Course key'] == course_key:
                threshold['week'] = row['Week']
                threshold['metric'] = row['Metric']
                threshold['target'] = row['Target']
                break

    # cleaning
    import os
    if os.path.exists('ltr-metrics.csv'):
        os.remove('ltr-metrics.csv')

    return threshold

# testing methods
def get_course_info_from_file2(course_key, week):
    """
    Get course details from S3 file
    """
    threshold = {}
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('pearson-prod')

    # download file
    with open('ltr-metrics.csv', 'wb') as data:
        temp = 'lt-target-per-course.csv'
        bucket.download_fileobj(temp, data)

    # reading file
    with open('ltr-metrics.csv', 'r') as csv_data:
        reader = csv.DictReader(csv_data)
        for row in reader:
            # set required look up
            conditions = [
                row['Course Key'] == course_key,
                row['Week'] == week,
            ]
            if all(conditions):
                threshold['cumulative_grade'] = float(row['Cumulative Grade'])
                threshold['timeliness_of_submissions'] = float(row['Timeliness'])
                threshold['average_session_length'] = float(row['Avg Session Length'])
                threshold['number_of_graded_assessment'] = float(row['Submissions'])
                threshold['time_between_sessions'] = float(row['Time btwn Sessions'])
                break

    # cleaning
    import os
    if os.path.exists('ltr-metrics.csv'):
        os.remove('ltr-metrics.csv')

    return threshold

def format_learner_record(record):
    record['cumulative_grade'] *= 100
    record['timeliness_of_submissions'] *= -1
    return record


def _get_edx_courses_data_from_csv():
    """
    Gets csv file from S3 and extracts the data.
    """
    amazon_resource = boto3.resource('s3')
    amazon_bucket = amazon_resource.Bucket('pearson-prod')
    previous = None
    data = {}

    for amazon_object in amazon_bucket.objects.filter(Prefix="daily-edx-log-files/"):

        if not previous or amazon_object.last_modified > previous:
            key = amazon_object.key
            previous = amazon_object.last_modified

    with open('aws-file.csv', 'wb') as csv_data:
        amazon_bucket.download_fileobj(key, csv_data)
        csv_data.close()
    with open('aws-file.csv', 'r') as csv_data:
        dict_reader = csv.DictReader(csv_data)
        for row in dict_reader:
            course_id = row['course_id']
            course_data = data.get(course_id, [])
            current_grade = row.get('current_grade', '0')
            user_id = row.get('id', '')

            user_data = {
                'username': row.get('user_username', ''),
                'email': row.get('user_email', ''),
                'user_id': int(user_id) if user_id else user_id,
                'cumulative_grade': float(current_grade) if current_grade else 0,
                'has_verified_certificate': row.get('has_passed', 'False') == 'True',
            }
            course_data.append(user_data)
            data[course_id] = course_data

        return data
