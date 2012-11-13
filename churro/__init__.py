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
_removed = object()


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
    __name__ = None
    __parent__ = None
    _fs = None

    def set_dirty(self):
        node = self
        while node is not None:
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
        if fs is None:
            return contents
        path = resource_path(self)
        if not fs.exists(path):
            return contents
        with fs.cd(path):
            for fname in fs.listdir():
                if fname == CHURRO_FOLDER:
                    continue
                if fs.isdir(fname):
                    folder_data = '%s/%s' % (fname, CHURRO_FOLDER)
                    if fs.exists(folder_data):
                        contents[fname] = ('folder', None)
                elif fname.endswith(CHURRO_EXT):
                    contents[fname[:-7]] = ('object', None)
        return contents

    @property
    def _filtered_contents(self):
        return {name: (type, obj) for name, (type, obj)
                in self._contents.items() if obj is not _removed}

    def keys(self):
        return self._filtered_contents.keys()

    def values(self):
        for name, value in self.items():
            yield value

    def __iter__(self):
        return iter(self._filtered_contents.keys())

    def items(self):
        contents = self._filtered_contents
        for name, (type, obj) in contents.items():
            if obj is None:
                obj = self._load(name, type)
            yield name, obj

    def __len__(self):
        return len(self._filtered_contents)

    def __nonzero__(self):
        return bool(self._filtered_contents)

    def __getitem__(self, name):
        obj = self.get(name, _marker)
        if obj is _marker:
            raise KeyError(name)
        return obj

    def get(self, name, default=None):
        contents = self._filtered_contents
        objref = contents.get(name)
        if not objref:
            return default
        type, obj = objref
        if obj is None:
            obj = self._load(name, type)
        return obj

    def _load(self, name, type, cache=True):
        if type == 'folder':
            fspath = resource_path(self, name, CHURRO_FOLDER)
        else:
            fspath = resource_path(self, name) + CHURRO_EXT
        obj = _marshal(self._fs.open(fspath, 'rb'))
        obj.__parent__ = self
        obj.__name__ = name
        obj._fs = self._fs
        obj._dirty = False
        if cache:
            self._contents[name] = (type, obj)
        return obj

    def __contains__(self, name):
        return name in self.keys()

    def __setitem__(self, name, other):
        type = 'folder' if isinstance(other, PersistentFolder) else 'object'
        self._contents[name] = (type, other)
        other.__parent__ = self
        other.__name__ = name
        other._fs = self._fs
        _set_dirty(other)

    def __delitem__(self, name):
        if not self._remove(name):
            raise KeyError(name)

    remove = __delitem__

    def pop(self, name, default=_marker):
        objref = self._remove(name)
        if not objref:
            if default is _marker:
                raise KeyError(name)
            return default

        type, obj = objref
        if obj:
            return obj
        return self._load(name, type, False)

    def _remove(self, name):
        contents = self._contents
        objref = contents.get(name)
        if objref:
            type, obj = objref
            if obj is _removed:
                return None
            contents[name] = (type, _removed)
            _set_dirty(self)
        return objref

    def _save(self):
        fs = self._fs
        path = resource_path(self)
        if not fs.exists(path):
            fs.mkdir(path)
        for name, (type, obj) in self._contents.items():
            if obj is None:
                continue
            if type == 'folder':
                if obj is _removed:
                    fs.rmtree(resource_path(self, name))
                else:
                    obj._save()
            else:
                fspath = resource_path(self, name) + CHURRO_EXT
                if obj is _removed:
                    fs.rm(fspath)
                else:
                    _serialize(obj, fs.open(fspath, 'wb'))
                    obj._dirty = False
        fspath = '%s/%s' % (path, CHURRO_FOLDER)
        _serialize(self, fs.open(fspath, 'wb'))
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

    tpc_abort = abort

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
            root._dirty = False
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


def resource_path(obj, *elements):
    def _inner(obj, path):
        if obj.__parent__ is not None:
            _inner(obj.__parent__, path)
            path.append(obj.__name__)
        return path
    path = _inner(obj, [])
    if elements:
        path.extend(elements)
    return '/' + '/'.join(path)


def _set_dirty(obj):
    while obj is not None:
        obj._dirty = True
        obj = obj.__parent__
