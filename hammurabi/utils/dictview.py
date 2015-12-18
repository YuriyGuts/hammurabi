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
        merged_object = self.merge_objects(self, other_object)
        self.__dict__ = merged_object.__dict__

    def merge_objects(self, obj1, obj2):
        dict1 = obj1.__dict__
        dict2 = obj2.__dict__
        result = ObjectDictView(dict())

        for k in set(dict1.keys()).union(dict2.keys()):
            if k in dict1 and k in dict2:
                if isinstance(dict1[k], ObjectDictView) and isinstance(dict2[k], ObjectDictView):
                    result.__dict__[k] = self.merge_objects(dict1[k], dict2[k])
                else:
                    # If one of the values is not a dict, we can't continue merging it.
                    # The value from the second dict overrides the one in the first and we move on.
                    result.__dict__[k] = dict2[k]
            elif k in dict1:
                result.__dict__[k] = dict1[k]
            else:
                result.__dict__[k] = dict2[k]

        return result
