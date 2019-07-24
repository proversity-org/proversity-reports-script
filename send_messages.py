"""
TODO
"""
from argparse import ArgumentParser
import os


def main():
    """
    TODO
    """
    parser = ArgumentParser()
    parser.add_argument(
        "--report",
        "-r",
        help="Get and upload the supported report.",
        required=True
    )
    parser.add_argument('--config-file', '-c', help='Path to configuration file.', required=True)
    parser.add_argument('--oauth-config-file', help='Path to the Google oAuth configuration file.', required=True)
    args = parser.parse_args()

    os.environ['CONFIGURATION_FILE_PATH'] = args.config_file
    os.environ['OAUTH_CONFIGURATION_FILE'] = args.oauth_config_file

    # init_report(args.report)


if __name__ == "__main__":
    main()
