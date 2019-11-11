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
            continue

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
def update_course_threshold(course_key, week, current_threshold):
    """
    Get course details from S3 file
    """
    threshold = {}
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('pearson-prod')

    # download file
    with open('ltr-metrics.csv', 'wb') as data:
        temp = 'px_lt_targets.csv'
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
                try:
                    current_threshold.get('cumulative_grade').update(
                        {'passing_score': float(row['Cumulative Grade'])}
                    )
                    current_threshold.get('average_session_length').update(
                        {'passing_score': float(row['Avg Session Length'])}
                    )
                    current_threshold.get('number_of_graded_assessment').update(
                        {'passing_score': float(row['Submissions'])}
                    )
                except Exception:
                    pass
                break

    # cleaning
    import os
    if os.path.exists('ltr-metrics.csv'):
        os.remove('ltr-metrics.csv')


def format_learner_record(record):
    record['cumulative_grade'] *= 100
    return record
