import json
from hammurabi.utils.dictview import ObjectDictView


def read_config(config_filename):
    try:
        with open(config_filename, "r") as config_file:
            config = ObjectDictView(json.load(config_file))
            return config
    except:
        print "Cannot load configuration file: {config_filename}".format(**locals())
        print
        raise
