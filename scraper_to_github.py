import argparse
import time

from github_operations import *
import requests
import os
from addoninfo import AddonInfo


def download_xpi(xpi_url: str, download_dir: str, unique_name: str):
    try:
        download_filepath = os.path.join(download_dir, unique_name)
        folder = os.path.dirname(download_filepath)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        response = requests.get(xpi_url, stream=True)
        print(f'download {unique_name} from {xpi_url}')
        with open(download_filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        return download_filepath
    except Exception as e:
        print(f'download {unique_name} from {xpi_url} failed: {e}')


def scrape_and_release(github_repository, addon_info: AddonInfo, **kwargs):
    if filepath := download_xpi(addon_info.xpi_url, download_dir='xpis', unique_name=addon_info.name):
        if release_id := create_release_and_delete_asset_if_need(
                github_repository=github_repository,
                tag_name=addon_info.tag_name,
                name=addon_info.name,
                github_token=kwargs.get('github_token')
        ):
            upload_xpi_to_release(github_repository=github_repository,
                                  release_id=release_id,
                                  upload_file_name=addon_info.name,
                                  upload_file=filepath,
                                  github_token=kwargs.get('github_token'))
    else:
        report_issue(github_repository,
                     title=f'{addon_info.name} xpi download failed',
                     body=f'xpi:{addon_info.name}\n'
                          f'url:{addon_info.xpi_url}\n',
                     github_token=kwargs.get('github_token'),
                     id=f'Download Failed: {addon_info.xpi_url}')


def do(input_dir, **kwargs):
    plugins = []
    for addon_json_filename in os.listdir(input_dir):
        if not addon_json_filename.endswith('.json'):
            continue
        addon_json_filepath = os.path.join(input_dir, addon_json_filename)
        with open(addon_json_filepath, 'r') as file:
            try:
                plugins.append(AddonInfo(**json.load(file)))
            except Exception as e:
                print(f'parse initial addon info from {addon_json_filepath} failed: {e}')

    for plugin in plugins:
        scrape_and_release(kwargs.get('github_repository'), plugin, github_token=kwargs.get('github_token'))
        time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='params')
    parser.add_argument('--github_repository', nargs='?', type=str, required=True, help='github repository')
    parser.add_argument('--github_token', nargs='?', type=str, help='github token')
    parser.add_argument('-i', '--input', nargs='?', type=str, default="addons", help='input addon dir')

    args = parser.parse_args()

    if not args.github_repository:
        raise 'Need specific github repository'

    if args.github_token:
        rate_limit(args.github_token)

    do(args.input, github_token=args.github_token, github_repository=args.github_repository)