import sys
import json
from urllib.parse import urlunparse, quote

import requests


def initialize(host='localhost', port=5984, username=None, password=None,
        ssl=False, databases=[]):
    server = Server(host, port, username, password, ssl)
    databases = \
        DatabasesDict(
            map(lambda name: (name, server[name]), databases))
    return server, databases


class DatabasesDict(dict):
    def __repr__(self):
        return repr(list(self.values()))
    def __str__(self):
        return str(list(self.values()))


class Resource(object):
    base = None
    username = None
    password = None

    def __init__(self, base=None, host=None, port=80, username=None,
            password=None, ssl=False):
        self.username = username
        self.password = password
        if base:
            self.base = base
        else:
            scheme = 'http'
            if ssl:
                sheme = 'https'
            self.base = urlunparse((scheme, host + ':' + str(port), '', None,
                None, None))

    def __getitem__(self, path):
        base = '/'.join([self.base, quote(path, '')])
        return self.__class__(base, username=self.username,
            password=self.password)

    def get(self, path=None, **kwargs):
        if path:
            return self[path].get(**kwargs)
        return self.request('GET', **kwargs)

    def post(self, path=None, **kwargs):
        if path:
            return self[path].post(**kwargs)
        return self.request('POST', **kwargs)

    def put(self, path=None, **kwargs):
        if path:
            return self[path].put(**kwargs)
        return self.request('PUT', **kwargs)

    def delete(self, path=None, **kwargs):
        if path:
            return self[path].delete(**kwargs)
        return self.request('DELETE', **kwargs)

    def head(self, path=None, **kwargs):
        if path:
            return self[path].head(**kwargs)
        return self.request('HEAD', **kwargs)

    def request(self, method, **kwargs):
        headers = kwargs.setdefault('headers', {})
        headers['Accept'] = 'application/json'
        if method in ('POST', 'PUT'):
            headers['Content-Type'] = 'application/json'
        if self.username or self.password:
            kwargs['auth'] = (self.username, self.password)
        response = requests.request(method, self.base, **kwargs)
        response.raise_for_status()
        return response

    def __str__(self):
        return '<Resource {}>'.format(self.base)
    __repr__ = __str__


class Server(object):
    def __init__(self, host='localhost', port=5984, username=None,
            password=None, ssl=False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.resource = Resource(host=host, port=port, username=username,
            password=password, ssl=ssl)

    def __setitem__(self, name, database):
        resource = self.resource[name]
        database.name = name
        database.resource = resource
        database.resource.put()

    def __getitem__(self, name):
        resource = self.resource[name]
        database = type('Database', (Database,), {'resource': resource})
        return database(name)

    def __str__(self):
        return '<Server host={} port={} username={} password={} ssl={} ' \
            'uuids={}>'.format(self.host, self.port, self.username,
            self.password, self.ssl, self.uuids)
    __repr__ = __str__


class Database(object):
    def __init__(self, name=None):
        self.name = name

    def __setitem__(self, _id, document):
        resource = self.resource[_id]
        if (isinstance(document, Document) and
                getattr(document, 'resource', None) is None):
            document.resource = resource
        response = resource.put(data=json.dumps(document))
        body = response.json()
        document['_id'] = body['id']
        document['_rev'] = body['rev']

    def __getitem__(self, _id):
        resource = self.resource[_id]
        document = type('Document', (Document,), {'resource': resource})
        response = document.resource.get()
        return document(**response.json())

    def __delitem__(self, _id):
        document = self[_id]
        document.resource.delete(params={'rev': document['_rev']})

    def __str__(self):
        return '<Database name={}>'.format(self.name)
    __repr__ = __str__


class Document(dict):
    def __repr__(self):
        return '<Document {}>'.format(super(Document, self).__repr__())
    def __str__(self):
        return '<Document {}>'.format(super(Document, self).__str__())
