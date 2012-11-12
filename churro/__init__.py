import acidfs
import json
import transaction

CHURRO_EXT = '.churro'
CHURRO_FOLDER = '__folder__' + CHURRO_EXT


class Churro(object):
    """
    **Constructor Arguments**

    ``repo``

       The path to the repository in the real, local filesystem.

    ``head``

       The name of a branch to use as the head for this transaction.  Changes
       made using this instance will be merged to the given head.  The default,
       if omitted, is to use the repository's current head.

    ``factory``

       A callable that returns the root database object to be stored as the
       root when creating a new database.  The default factory returns an
       instance of `churro.PersistentFolder`.

    ``create``

       If there is not a Git repository in the indicated directory, should one
       be created?  The default is `True`.

    ``bare``

       If the Git repository is to be created, create it as a bare repository.
       If the repository is already created or `create` is False, this argument
       has no effect.
    """
    session = None

    def __init__(self, repo, head='HEAD',
                 factory=None, create=True, bare=False):
        self.fs = acidfs.AcidFS(repo, head=head, create=create, bare=bare,
                                name='Churro.AcidFS')
        if factory is None:
            factory = PersistentFolder
        self.factory = factory

    def _session(self):
        """
        Make sure we're in a session.
        """
        if not self.session or self.session.closed:
            self.session = _Session(self.fs)
        return self.session

    def root(self):
        return self._session().get_root(self.factory)


_marker = object()


class reify(object):
    # Stolen from Pyramid
    """ Put the result of a method which uses this (non-data)
    descriptor decorator in the instance dict after the first call,
    effectively replacing the decorator with an instance variable."""

    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except: # pragma: no cover
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


class PersistentType(type):

    def __init__(cls, name, bases, members):
        type.__init__(cls, name, bases, members)
        for name, prop in members.items():
            if isinstance(prop, PersistentProperty):
                prop.set_name(name)


class PersistentProperty(object):

    def set_name(self, name):
        self.attr = '.' + name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.attr)

    def __set__(self, obj, value):
        obj.set_dirty()
        return setattr(obj, self.attr, self.validate(value))

    def from_json(self, value):
        return value

    def to_json(self, value):
        return value

    def validate(self, value):
        return value


class Persistent(object):
    __metaclass__ = PersistentType
    _dirty = True

    def set_dirty(self):
        node = self
        while node:
            node._dirty = True
            node = getattr(node, '__parent__', None)

    def _serialize(self, stream):
        data = {}
        for cls in type(self).mro():
            for name, prop in cls.__dict__.items():
                if not isinstance(prop, PersistentProperty):
                    continue
                if name not in data:
                    data[name] = prop.to_json(prop.__get__(self))
        json.dump(data, stream)

    def _marshal(self, stream):
        cls = type(self)
        data = json.load(stream)
        for name, value in data.items():
            prop = getattr(cls, name)
            prop.__set__(self, prop.from_json(value))


class PersistentFolder(Persistent):

    @reify
    def _contents(self):
        contents = {}
        fs = self._fs
        with fs.cd(resource_path(self)):
            for fname in fs.listdir():
                if fs.isdir(fname):
                    folder_data = '%s/%s' % (fname, CHURRO_FOLDER)
                    if fs.exists(folder_data):
                        contents[fname] = ('folder', None)
                elif fname.endswith(CHURRO_EXT):
                    contents[fname[:-7]] = ('object', None)
        return contents

    def keys(self):
        return self._contents.keys()

    def values(self):
        contents = self._contents
        for name, (type, obj) in self._contents.items():
            if obj is None:
                obj = self._load(type, name)
                contents[name] = (type, obj)
            yield obj

    def __iter__(self):
        return iter(self._contents.keys())

    def items(self):
        pass

    def __len__(self):
        return len(self._contents)

    def __nonzero__(self):
        return bool(self._contents)

    def __getitem__(self, name):
        obj = self.get(name, _marker)
        if obj is _marker:
            raise KeyError(name)
        return obj

    def get(self, name, default=None):
        contents = self._contents
        objref = contents.get(name)
        if not objref:
            return default
        type, obj = objref
        if obj is None:
            here = resource_path(self)
            if type == 'folder':
                fspath = '%s/%s/%s' % (here, name, CHURRO_FOLDER)
            else:
                fspath = '%s/%s%s' % (here, name, CHURRO_EXT)
            obj = _marshal(self._fs.open(fspath, 'rb'))
            obj.__parent__ = self
            obj.__name__ = name
            contents[name] = (type, obj)
        return obj

    def __contains__(self, name):
        return name in self.keys()

    def __setitem__(self, name, other):
        type = 'folder' if isinstance(other, PersistentFolder) else 'object'
        self._contents[name] = (type, other)
        other.__parent__ = self
        other.__name__ = name
        _set_dirty(other)

    def __delitem__(self, name):
        pass

    remove = __delitem__

    def pop(self, name, default=_marker):
        pass

    def _save(self):
        for name, (type, obj) in self._contents.items():
            if obj is None:
                continue
            if type == 'folder':
                obj._save()
            else:
                fspath = resource_path(obj) + CHURRO_EXT
                _serialize(obj, self._fs.open(fspath, 'wb'))
                obj._dirty = False
        fspath = '%s/%s' % (resource_path(self), CHURRO_FOLDER)
        _serialize(self, self._fs.open(fspath, 'wb'))
        self._dirty = False

    #def __repr__(self):
    #    pass


class _Session(object):
    closed = False
    root = None

    def __init__(self, fs):
        self.fs = fs
        transaction.get().join(self)

    def abort(self, tx):
        """
        Part of datamanager API.
        """
        self.close()

    def tpc_begin(self, tx):
        """
        Part of datamanager API.
        """

    def commit(self, tx):
        """
        Part of datamanager API.
        """

    def tpc_vote(self, tx):
        """
        Part of datamanager API.
        """
        root = self.root
        if root is None or not root._dirty:
            # Nothing to do
            return

        root._save()

    def tpc_finish(self, tx):
        """
        Part of datamanager API.
        """

    def tpc_abort(self, tx):
        """
        Part of datamanager API.
        """
        self.close()

    def sortKey(self):
        return 'Churro'

    def close(self):
        self.closed = True

    def get_root(self, factory):
        if self.root is not None: # is not None
            return self.root

        fs = self.fs
        path = '/' + CHURRO_FOLDER
        if fs.exists(path):
            root = _marshal(fs.open(path, 'rb'))
        else:
            root = factory()
        root._fs = fs
        root.__name__ = root.__parent__ = None
        self.root = root
        return root


def _marshal(stream):
    dotted_name = unicode(next(stream), 'utf8').strip()
    cls = _resolve_dotted_name(dotted_name)
    obj = cls.__new__(cls)
    obj._marshal(stream)
    return obj


def _serialize(obj, stream):
    cls = type(obj)
    dotted_name = '%s.%s\n' % (cls.__module__, cls.__name__)
    stream.write(dotted_name.encode('utf8'))
    obj._serialize(stream)


def _resolve_dotted_name(name):
    names = name.split('.')
    path = names.pop(0)
    target = __import__(path)
    while names:
        segment = names.pop(0)
        path += '.' + segment
        try:
            target = getattr(target, segment)
        except AttributeError:
            __import__(path)
            target = getattr(target, segment)
    return target


def resource_path(obj):
    def _inner(obj, path):
        if obj.__parent__ is not None:
            _inner(obj.__parent__, path)
            path.append(obj.__name__)
        return path
    return '/' + '/'.join(_inner(obj, []))


def _set_dirty(obj):
    while obj:
        obj._dirty = True
        obj = obj.__parent__
