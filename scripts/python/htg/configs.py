import json
import os


class Configs:
    """Super Simple Configs Class"""

    htg_basedir = os.getenv('HTG_BASEDIR')
    config_list = ['default', 'user']
    config_filepaths = {
        'default': '{}/.baseconfigs'.format(htg_basedir),
        'user': '{}/.userconfigs'.format(htg_basedir)
    }

    default_data = {}
    default_config_keys = []
    user_data = {}
    user_config_keys = []

    def __init__(self):
        self.read_configs()

    def get_config(self, config_name):
        if config_name in self.user_config_keys:
            return self.user_data[config_name]
        elif config_name in self.default_config_keys:
            return self.default_data[config_name]
        else:
            return None

    def set_config(self, config_name, value):
        self.user_data[config_name] = value
        if config_name not in self.user_config_keys:
            self.user_config_keys.append(config_name)
        self.write_config()

    def clear_config(self, config_name):
        x = self.user_data.pop(config_name)
        self.write_config()

    def read_configs(self):
        file = open(self.config_filepaths['default'], 'r')
        self.default_data = json.load(file)
        file.close()

        try:
            file = open(self.config_filepaths['user'], 'r')
            self.user_data = json.load(file)
            file.close()
        except FileNotFoundError:
            self.user_data = {}
            self.write_config()

        self.default_config_keys = self.default_data.keys()
        self.user_config_keys = self.user_data.keys()

    def write_config(self):
        file = open(self.config_filepaths['user'], 'w')
        json.dump(self.user_data, file)
        file.close()
