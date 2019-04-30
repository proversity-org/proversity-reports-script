import os
import requests
from argparse import ArgumentParser, FileType
import json

from request_report import init_report


def main():
    parser = ArgumentParser()
    parser.add_argument("--report", "-r", help="Get and upload the completion report.", required=True)
    parser.add_argument('--config-file', '-c', help='Path to configuration file.', required=True)
    args = parser.parse_args()

    os.environ['CONFIGURATION_FILE_PATH'] = args.config_file

    init_report(args.report)

if __name__ == "__main__":
    main()
