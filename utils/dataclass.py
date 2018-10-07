from dataclasses import dataclass
from dataclasses import fields


def from_dict(cls: dataclass, dictionary: dict):
    """Make dataclass object from a dictionary.

    :param cls: The dataclass to make a object of.
    :param dictionary: The dictionary.
    :return: The dataclass object.
    """
    init_kwargs = {}
    for _field in fields(cls):
        field_value = dictionary.get(_field.name)
        init_kwargs[_field.name] = field_value
    return cls(**init_kwargs)
