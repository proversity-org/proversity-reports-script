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
            "BACKEND_REPORT": "example:report_backend.completion_report:CompletionReportBackend",
            "SPREADSHEET_DATA": {
                "completion_sheet_id_<course_id>": "Spreadsheet id for completion report.",
                "general_course_sheet_id_<course_id>": "Spreadsheet id for course structure report."
            }
        },
        "LAST_PAGE_ACCESSED": {
            "REPORT_URL": "path-to-report-generation-url",
            "BACKEND_REPORT": "absolute-path-to-report-backend-module:report-backend-class-name"
            "SPREADSHEET_DATA": {
                 "last_page_accessed_table_<course_id>": "Spreadsheet id for last page accessed report.",
                "last_page_accessed_bar_char_<course_id>": "Spreadsheet id for last page accessed report.",
            }
        },
        "TIME_SPENT_REPORT": {
            "REPORT_URL": "path-to-report-generation-url",
            "BACKEND_REPORT": "absolute-path-to-report-backend-module:report-backend-class-name",
            "SPREADSHEET_DATA": {
                "time_spent_sheet_id_<course_id>": "Spreadsheet id for time spent report."
            }
        },
        "Add a new key in uppercase according to the new SUPPORTED_REPORTS value.
        The new key must have the keys REPORT_URL and BACKEND_REPORT."
        "COURSES": [
            course-id
        ],
        "GOOGLE_OAUTH_CREDENTIALS": {
            "installed": {
                "client_id": "Google oAuth client ID",
                "project_id": "Google console project ID",
                "auth_uri": "oAuth uri",
                "token_uri": "oAuth token uri",
                "auth_provider_x509_cert_url": "String",
                "client_secret": "Google oAuth client secret",
                "redirect_uris": [
                    "Google oAuth urls"
                ]
            }
        }
    }

GOOGLE_OAUTH_CREDENTIALS came from downloaded Google oAuth credentials in json format.

## Running

python3 ./fetch_report.py --report "supported-report-name" --config-file "path-to-config-file" --oauth-config-file "path-to-google-oauth-credentials-file"

## Get Goolge oAuth credentials

This command creates a new file called "google-oauth-credentials.json" containing the
authorized Google oAuth credentials. (token)

python3 ./get_google_oauth_permissions.py --config-file "path-to-config-file"
