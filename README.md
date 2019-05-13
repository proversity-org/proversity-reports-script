# Proversity reports script

## Installation

pip install pipenv
python3 -m venv venv
source venv/bin/activate
pipenv install

## Configuration

The configuration file must be in json format. e.g.

{
    "LMS_URL": "path-to-lms-running-server",
    "OPEN_EDX_OAUTH_TOKEN": "oAuth-lms-token",
    "AWS_ACCESS_KEY_ID": "S3-AWS-access-key",
    "AWS_SECRET_ACCESS_KEY": "S3-AWS-secret-key",
    "SUPPORTED_REPORTS": [
        "completion_report",
        "last_page_accessed",
        "time_spent_report",
        "Add a new one, if you add a new report backend"
    ],
    "COMPLETION_REPORT": {
        "REPORT_URL": "example:/proversity-reports/api/v0/generate-completion-report",
        "BACKEND_REPORT": "example:report_backend.completion_report:CompletionReportBackend"
    },
    "LAST_PAGE_ACCESSED": {
        "REPORT_URL": "path-to-report-generation-url",
        "BACKEND_REPORT": "absolute-path-to-report-backend-module:report-backend-class-name"
    },
    "TIME_SPENT_REPORT": {
        "REPORT_URL": "path-to-report-generation-url",
        "BACKEND_REPORT": "absolute-path-to-report-backend-module:report-backend-class-name"
    },
    "Add a new key in uppercase according to the new SUPPORTED_REPORTS value.
    The new key must have the keys REPORT_URL and BACKEND_REPORT."
    "COURSES": [
        course-id
    ]
}

## Running

python3 ./fetch_report.py --report "supported-report-name" --config-file "path-to-config-file"
