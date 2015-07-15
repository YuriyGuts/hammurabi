class ObjectDictView:
    """Creates an object-like representation of a dictionary which can also contain nested lists or dictionaries."""

    def __init__(self, dictionary):
        self.__dict__ = dictionary

        keys = self.__dict__.keys()
        for key in keys:
            # Recursively convert sub-dictionaries to object-like representations.
            if isinstance(self.__dict__[key], dict):
                self.__dict__[key] = ObjectDictView(self.__dict__[key])

            # If we have an array, iterate through it and convert sub-dictionaries if there are any.
            if isinstance(self.__dict__[key], list):
                self.__dict__[key] = [ObjectDictView(item) if isinstance(item, dict) else item
                                      for item in self.__dict__[key]]

    def get_safe(self, key, default_value=None):
        key_parts = key.split("/")
        current_dict = self

        for key in key_parts:
            if key in current_dict.__dict__:
                current_dict = current_dict.__dict__[key]
            else:
                return default_value

        return current_dict

    def merge(self, other_object):
        self.__dict__.update(other_object.__dict__)
