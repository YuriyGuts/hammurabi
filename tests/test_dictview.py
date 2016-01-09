import pytest
from hammurabi.utils.dictview import ObjectDictView


def test_init_when_passed_an_empty_dictionary_creates_an_empty_object():
    # Arrange
    empty_dict = {}

    # Act
    dict_view = ObjectDictView(empty_dict)

    # Assert
    assert len(vars(dict_view)) == 0


def test_init_when_passed_a_flat_dictionary_creates_a_flat_object():
    # Arrange
    flat_dict = {
        "foo": 1,
        "bar": 2,
    }

    # Act
    dict_view = ObjectDictView(flat_dict)

    # Assert
    assert len(vars(dict_view)) == len(flat_dict)
    assert hasattr(dict_view, "foo")
    assert hasattr(dict_view, "bar")
    assert dict_view.foo == 1
    assert dict_view.bar == 2


def test_init_when_passed_an_array_value_creates_an_array_property():
    # Arrange
    dict_with_array = {
        "foo": 1,
        "bars": [2, 3, 4, 5, 6]
    }

    # Act
    dict_view = ObjectDictView(dict_with_array)

    # Assert
    assert len(vars(dict_view)) == len(dict_with_array)
    assert isinstance(dict_view.bars, list)
    assert len(dict_view.bars) == 5


def test_init_when_passed_a_nested_dictionary_creates_a_nested_object():
    # Arrange
    nested_dict = {
        "level1prop1": 1,
        "level2": {
            "level2prop1": 2,
            "level3": {
                "level3prop1": 3,
            }
        }
    }

    # Act
    dict_view = ObjectDictView(nested_dict)

    # Assert
    assert len(vars(dict_view)) == 2
    assert dict_view.level1prop1 == 1

    assert isinstance(dict_view.level2, ObjectDictView)
    assert len(vars(dict_view.level2)) == 2
    assert dict_view.level2.level2prop1 == 2

    assert isinstance(dict_view.level2.level3, ObjectDictView)
    assert len(vars(dict_view.level2.level3)) == 1
    assert dict_view.level2.level3.level3prop1 == 3


def test_get_safe_when_passed_an_existing_key_returns_its_value():
    # Arrange
    nested_dict = {
        "level1prop1": 1,
        "level2": {
            "level2prop1": 2,
            "level3": {
                "level3prop1": 3,
            }
        }
    }
    dict_view = ObjectDictView(nested_dict)

    # Act
    value = dict_view.get_safe("level2/level3/level3prop1")

    # Assert
    assert value == 3


def test_get_safe_when_passed_a_nonexistent_key_returns_default_value():
    # Arrange
    nested_dict = {
        "level1prop1": 1,
        "level2": {
            "level2prop1": 2,
            "level3": {
                "level3prop1": 3,
            }
        }
    }
    dict_view = ObjectDictView(nested_dict)

    # Act
    value1 = dict_view.get_safe("level2/level3/level4/level4prop1")
    value2 = dict_view.get_safe("level2/level3/level4/level4prop1", default_value=42)

    # Assert
    assert value1 is None
    assert value2 == 42


def test_merge_two_disjoint_objects_returns_a_union_object():
    # Arrange
    nested_dict1 = {
        "level1prop1": 1,
        "level2": {
            "level2prop1": 2,
            "level3": {
                "level3prop1": 3,
            }
        }
    }

    nested_dict2 = {
        "level1prop2": 4,
        "level2": {
            "level2prop2": 5,
            "level3": {
                "level3prop2": 6,
            }
        }
    }

    dict_view1 = ObjectDictView(nested_dict1)
    dict_view2 = ObjectDictView(nested_dict2)

    # Act
    dict_view1.merge(dict_view2)

    # Assert
    assert dict_view1.level1prop1 == 1
    assert dict_view1.level1prop2 == 4
    assert dict_view1.level2.level2prop1 == 2
    assert dict_view1.level2.level2prop2 == 5
    assert dict_view1.level2.level3.level3prop1 == 3
    assert dict_view1.level2.level3.level3prop2 == 6


def test_merge_overlapped_objects_second_object_takes_priority():
    # Arrange
    nested_dict1 = {
        "level1prop1": 1,
        "level2": {
            "level2prop1": 2,
            "level3": {
                "level3prop1": 3,
            }
        }
    }

    nested_dict2 = {
        "level1prop1": 4,
        "level2": {
            "level2prop1": 5,
            "level3": {
                "level3prop2": 6,
            }
        }
    }

    dict_view1 = ObjectDictView(nested_dict1)
    dict_view2 = ObjectDictView(nested_dict2)

    # Act
    dict_view1.merge(dict_view2)

    # Assert
    assert dict_view1.level1prop1 == 4
    assert dict_view1.level2.level2prop1 == 5
    assert dict_view1.level2.level3.level3prop1 == 3
    assert dict_view1.level2.level3.level3prop2 == 6
