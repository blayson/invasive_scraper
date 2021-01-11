import json
import os

import requests

from settings import CATEGORY_URLS, HEADERS, CATEGORY_URLS_INVASIVE


def parse_bugworld_response(data):
    return [{'id': item[0], 'name': item[1], 'scientific_name': item[2]} for item in data['data']]


def parse_invasive_api(data):
    return [{'id': item['SUB_ID'], 'name': item['SUB_NAME'], 'scientific_name': item['SUB_GENUS']} for item in data['data']]


def get_categories_from_api(url: str, parser):
    resp = requests.get(url, headers=HEADERS)

    json_content = {}
    if resp.status_code == 200:
        json_content = json.loads(resp.content)

    result = parser(json_content)

    print('data length: ' + str(len(result)))
    return result


def save_to_file(file_name: str, data):
    with open(file_name, 'w') as json_file:
        json.dump(data, json_file)
    print('OK.')


def download(urls: dict, parser):
    for category, url_dict in urls.items():
        for name, link in url_dict.items():
            categories = get_categories_from_api(link, parser=parser)
            try:
                os.mkdir('categories/{}'.format(category))
            except FileExistsError:
                pass
            save_to_file('categories/{}/{}.json'.format(category, name), categories)


if __name__ == '__main__':
    download(CATEGORY_URLS, parser=parse_bugworld_response)
    download(CATEGORY_URLS_INVASIVE, parser=parse_invasive_api)
