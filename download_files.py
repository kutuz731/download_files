#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания файлов заданных типов с сайта (http/https) с обходом вложенных папок.
Использование:
    python download_files.py -u <base_url> [-o download_dir] [-t types]
Где:
    -u, --url       базовый URL сайта (обязательный)
    -o, --output    директория для сохранения (по умолчанию downloaded_files)
    -t, --types     через запятую список расширений без точки (jpg,png,pdf) или 'all' для всех файлов
Примеры:
    python download_files.py -u http://192.168.1.234:8080 -o images -t pdf,jpg,png
    python download_files.py --url https://example.com --types all
"""

import os
import sys
import requests
import urllib3
import argparse
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser(description='Скрипт для скачивания файлов заданных типов с сайта')
parser.add_argument('-u', '--url', required=True, help='Базовый URL сайта (http/https)')
parser.add_argument('-o', '--output', default='downloaded_files', help='Директория для сохранения файлов')
parser.add_argument('-t', '--types', default='jpg,png,jpeg,gif,bmp,webp',
                    help="Список расширений через запятую без точки или 'all' для всех файлов")
args = parser.parse_args()

BASE_URL = args.url.rstrip('/')
DOWNLOAD_DIR = args.output

types_arg = args.types.strip()
if types_arg.lower() == 'all':
    FILE_EXTS = None
else:
    FILE_EXTS = {'.' + ext.lower() for ext in types_arg.split(',') if ext}


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def download_file(url, local_path):
    resp = requests.get(url, stream=True, verify=False)
    resp.raise_for_status()
    with open(local_path, 'wb') as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    print(f'Downloaded: {local_path}')


def crawl_folder(path=''):
    api_url = f"{BASE_URL}/api/browse/{quote(path)}" if path else f"{BASE_URL}/api/browse"
    try:
        r = requests.get(api_url, verify=False)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error accessing API {api_url}: {e}")
        return

    local_folder = os.path.join(DOWNLOAD_DIR, path)
    ensure_dir(local_folder)

    for folder in data.get('folders', []):
        subpath = f"{path}/{folder}" if path else folder
        crawl_folder(subpath)

    for fname in data.get('images', []):
        ext = os.path.splitext(fname)[1].lower()
        if FILE_EXTS is None or ext in FILE_EXTS:
            rel_path = f"{path}/{fname}" if path else fname
            file_url = f"{BASE_URL}/{quote(rel_path)}"
            local_file = os.path.join(DOWNLOAD_DIR, rel_path)
            ensure_dir(os.path.dirname(local_file))
            try:
                download_file(file_url, local_file)
            except Exception as e:
                print(f"Error downloading {file_url}: {e}")

if __name__ == '__main__':
    print(f"Base URL: {BASE_URL}\nOutput Dir: {DOWNLOAD_DIR}\nTypes: {'all' if FILE_EXTS is None else ','.join(sorted(FILE_EXTS))}\n")
    crawl_folder()
