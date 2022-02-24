"""Read in the TS assets"""

import json
import os


def get_assets(ts_directory):
    # TODO: In the future there will likely be other directories to import
    ts_indexfile = os.path.join(ts_directory, 'Taleweaver', 'd71427a1-5535-4fa7-82d7-4ca1e75edbfd', 'index.json')

    file = open(ts_indexfile, 'r')
    data = file.read()
    file.close()

    index_dict = json.loads(data)

    return index_dict
