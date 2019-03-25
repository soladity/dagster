from abc import ABCMeta, abstractmethod
import pickle

import six

from dagster import check


@six.add_metaclass(ABCMeta)
class SerializationStrategy:
    @abstractmethod
    def serialize_value(self, value, write_file_obj):
        pass

    @abstractmethod
    def deserialize_value(self, read_file_obj):
        pass


class PickleSerializationStrategy(SerializationStrategy):
    def serialize_value(self, value, write_file_obj):
        pickle.dump(value, write_file_obj)

    def deserialize_value(self, read_file_obj):
        return pickle.load(read_file_obj)


def serialize_to_file(serialization_strategy, value, write_path):
    check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
    check.str_param(write_path, 'write_path')

    with open(write_path, 'wb') as write_obj:
        return serialization_strategy.serialize_value(value, write_obj)


def deserialize_from_file(serialization_strategy, read_path):
    check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)
    check.str_param(read_path, 'read_path')

    with open(read_path, 'rb') as read_obj:
        return serialization_strategy.deserialize_value(read_obj)
