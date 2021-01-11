#!/usr/bin/env python
import os
import math
import shutil
import time
import json
import pathlib
import zipfile

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from settings import IMG_URL, HEADERS, RESOLUTIONS, EXT, IMAGE_INFO_URLS, URL_VIRUSES


# session = requests.Session()


def download_image(img_id, path: str):
    full_url = IMG_URL.format(resolution=RESOLUTIONS['large'], img_num=img_id, ext=EXT)
    resp = requests.get(full_url, stream=True, headers=HEADERS)

    print('image download status: ' + str(resp.status_code))

    if resp.status_code == 200:
        ts = time.time()
        back = ''
        if 'images' not in os.listdir():
            back = '../'
            if 'images' not in os.listdir():
                back = '../../'
        pathlib.Path('{}images/{}'.format(back, path)).mkdir(parents=True, exist_ok=True)
        with open('{}images/{}/{}.{}'.format(back, path, ts, EXT), 'wb') as f:
            resp.raw.decode_content = True
            shutil.copyfileobj(resp.raw, f)
        return True
    return False


def get_image_data_from_api(url):
    print('request: ' + url)

    r = requests.get(url, headers=HEADERS)

    print('image info: ' + str(r.status_code))
    if r.status_code == 200 and r.content:
        return json.loads(r.content)['rows']
    else:
        return None


def get_data_from_api(dir_, file_name):
    output_data = []
    # print(file_name)
    if file_name in ['common_diseases.json', 'abiotic_damage.json']:
        with open('{}'.format(file_name), 'r') as f:
            sub_categories = json.load(f)
            for sub in sub_categories:
                data = get_image_data_from_api(IMAGE_INFO_URLS[dir_][file_name.split('.')[0]].format(sub_id=sub['id']))

                print('data length: ' + str(len(data)))

                output_data.extend(prepare(data, dir_))
    else:
        i = 1
        while True:
            data = get_image_data_from_api(IMAGE_INFO_URLS[dir_][file_name.split('.')[0]].format(page=i))
            print('data length: ' + str(len(data)))
            i += 1
            if data is None or len(data) == 0:
                break
            else:
                output_data.extend(prepare(data, dir_))
    return output_data


def prepare(data, dir_):
    output_data = []
    for item in data:
        output_data.append({
            'category': dir_,
            'subject': item['sub_name'],
            'id': item['imgnum'],
            'url': IMG_URL.format(resolution=RESOLUTIONS['large'], img_num=item['imgnum'], ext=EXT),
        })

        download_image(item['imgnum'], '{}/{}'.format(dir_, item['sub_name']))
    return output_data


def write_output(dir_, file_name, data, back=''):
    pathlib.Path('{}data/{}'.format(back, dir_)).mkdir(parents=True, exist_ok=True)

    with open('{}data/{}/{}'.format(back, dir_, file_name), 'w') as f:
        json.dump(data, f)
        print('Data successfully saved to {}/{}'.format(dir_, file_name))


def scrape_html():
    range_ = math.ceil(4300 / 200)
    print('range: ' + str(range_))

    start = 1
    result = []
    for i in range(int(range_)):
        print('page: ' + str(i+1))
        print('start index: ' + str(start))

        r = requests.get(URL_VIRUSES + '&start=' + str(start), headers=HEADERS)
        soup = BeautifulSoup(r.content, 'html.parser')

        data = []
        for div in soup.find_all('div', class_='col-xs-12 col-sm-6 col-md-4 text-center'):
            img_num = div.find('img').get('alt')
            sub_name = ''
            for br in div.findAll('br'):
                next_s = br.nextSibling
                if not (next_s and isinstance(next_s, NavigableString)):
                    continue
                next2_s = next_s.nextSibling
                if next2_s and isinstance(next2_s, Tag) and next2_s.name == 'br':
                    sub_name = str(next_s).strip()
                    break
            data.append({'imgnum': img_num, 'sub_name': sub_name})

        result.append(prepare(data, 'viruses'))
        start = start + 200
    return result


def run():
    print('Start scraping data from api...')

    current_dir = os.getcwd()
    os.chdir('{}/categories'.format(current_dir))
    dirs = os.listdir()

    print(dirs)
    for dir_ in dirs:
        os.chdir(dir_)
        print(os.getcwd())
        files = os.listdir()
        for file in files:
            data = get_data_from_api(dir_, file)
            write_output(dir_, file, data, '../../')
        os.chdir('..')
    os.chdir('..')

    print('Start scraping data from html...')

    data = scrape_html()
    write_output('viruses', 'viruses.json', data)

    print('Done.')

    ts = time.time()
    zipf = zipfile.ZipFile('images_{}.zip'.format(ts), 'w', zipfile.ZIP_DEFLATED)
    zipdir('images', zipf)
    zipf.close()


def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))


if __name__ == '__main__':
    run()
