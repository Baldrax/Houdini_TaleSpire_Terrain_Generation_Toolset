# This Code is adapted from https://github.com/LuPro/SlabelFish
"""Read in the TS assets"""

import json
import os


def get_assets(ts_directory):
    ts_index_files = list()
    taleweaver_dir = os.path.join(ts_directory, 'Taleweaver')

    # Get a list of all the Taleweaver asset databases
    for root, dirs, files in os.walk(taleweaver_dir):
        if 'index.json' in files:
            ts_index_files.append(os.path.join(root, 'index.json'))

    index_dict_list = list()

    for ts_index_file in ts_index_files:
        file = open(ts_index_file, 'r')
        data = file.read()
        file.close()

        index_dict_list.append(json.loads(data))

    return index_dict_list
