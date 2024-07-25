# -*- coding: utf-8 -*-
"""
Project Name: data_clean
File Created: 2024.07.22
Author: ZhangYuetao
File Name: utils.py
last renew 2024.07.22
"""

import os
import json


def get_image_files(dir_path):
    image_files = []
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.img')
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(image_extensions):
                image_files.append(os.path.join(root, file))
    return image_files


def read_json(file_path, default_value):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError:
            pass
    return default_value


def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
