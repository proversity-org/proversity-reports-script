"""
Main module for additional proversity reports.
"""
from argparse import ArgumentParser
import os

from proversity_reports_script.request_report import init_report  # pylint: disable=relative-import


def main():
    """
    Main entry point of the script report generation.
    """
    parser = ArgumentParser()
    parser.add_argument(
        "--report",
        "-r",
        help="Get and upload the supported report.",
        required=True
    )
    parser.add_argument('--config-file', '-c', help='Path to configuration file.', required=True)
    args = parser.parse_args()

    os.environ['CONFIGURATION_FILE_PATH'] = args.config_file

    init_report(args.report)


if __name__ == "__main__":
    main()
