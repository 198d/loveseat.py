from datetime import datetime, date

from loveseat import Document, get_server, get_database


class Property(object):
    name = None

    def __init__(self, default=None):
        self.default = default

    def __get__(self, instance, cls):
        if instance is None:
            return self

        value = instance.__document__.get(self.name, None)
        if value is not None:
            return self.to_python(value)
        elif self.default is not None:
            value = self.default
            if callable(self.default):
                value = self.default()
            self.__set__(instance, value)
            return value
        return None

    def __set__(self, instance, value):
        if instance is None:
            return
        instance.__document__[self.name] = self.to_json(value)

    def to_python(self, value):
        return value

    def to_json(self, value):
        return str(value)


class String(Property):
    def to_python(self, value):
        return str(value)


class Integer(Property):
    def to_python(self, value):
        return int(value)

    def to_json(self, value):
        return int(value)


class Float(Property):
    def to_python(self, value):
        return float(value)

    def to_json(self, value):
        return float(value)


class Date(Property):
    def to_python(self, value):
        return datetime.strptime(value, '%Y-%m-%d').date()

    def to_json(self, value):
        return value.isoformat()


class DateTime(Property):
    def to_python(self, value):
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')

    def to_json(self, value):
        return value.replace(microsecond=0).isoformat()


class Dict(Property):
    def __init__(self, default=dict):
        super(Dict, self).__init__(default=default)

    def to_json(self, value):
        return value


class List(Property):
    def __init__(self, default=list):
        super(List, self).__init__(default=default)

    def to_json(self, value):
        return value


class Boolean(Property):
    def to_json(self, value):
        return bool(value)


class Id(String):
    def __set__(self, instance, value):
        prefix = self.prefix(instance.__class__)
        if not value.startswith(prefix):
            value = prefix + value
        super(Id, self).__set__(instance, value)

    def __get__(self, instance, cls):
        value = super(Id, self).__get__(instance, cls)
        if value is None:
            value = self.prefix(cls) + get_server().uuids.pop()
            self.__set__(instance, value)
        return value

    @staticmethod
    def prefix(cls):
        return cls.__name__ + ':'


class MapperMeta(type):
    def __new__(cls, name, bases, attrs):
        schema = {}

        for base in bases:
            base_schema = getattr(base, '__schema__', {})
            schema.update(base_schema)

        for attr, value in attrs.items():
            if isinstance(value, Property):
                schema[attr] = value
                setattr(value, 'name', attr)
        attrs['__schema__'] = schema
        return type.__new__(cls, name, bases, attrs)


Base = MapperMeta('DocumentMapperBase', (object,), {})
class MapperBase(Base):
    _id = Id()
    _rev = String()

    def __init__(self, **kwargs):
        self.__document__ = Document()
        for key, value in kwargs.items():
            if key in self.__schema__:
                self.__schema__[key].__set__(self, value)
            else:
                self.__document__[key] = value

    @classmethod
    def get(cls, _id, database=None):
        if database is None:
            database = getattr(cls, '__database__', get_database())
        instance = cls()
        instance.__document__ = database[_id]
        return instance

    def put(self, database=None):
        if database is None:
            database = getattr(self, '__database__', get_database())
        for property in self.__schema__.keys():
            getattr(self, property)
        database[self._id] = self.__document__
