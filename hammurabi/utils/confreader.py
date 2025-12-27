import json

from hammurabi.utils.dictview import ObjectDictView


def read_config(config_filename):
    try:
        with open(config_filename) as config_file:
            config = ObjectDictView(json.load(config_file))
            return config
    except:
        print(f"Cannot load configuration file: {config_filename}")
        print()
        raise
