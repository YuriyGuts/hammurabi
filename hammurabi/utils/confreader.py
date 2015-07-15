import json
import os
from hammurabi.utils.dictview import ObjectDictView


def read_config(config_filename):
    if not os.path.exists(config_filename):
        return ObjectDictView({})

    try:
        with open(config_filename, "r") as config_file:
            config = ObjectDictView(json.load(config_file))
            return config
    except:
        print "Cannot load configuration file: {config_filename}".format(**locals())
        print
        raise
