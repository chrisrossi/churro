

class DictWrapper(object):
    def __init__(self, *args):
        self.data = dict(*args)

    def __contains__(self, key):
        return self.data.__contains__(key)

    def __delitem__(self, key):
        self.mutated()
        return self.data.__delitem__(key)

    def __eq__(self, other):
        return self.data.__eq__(self._cast(other))

    def __getitem__(self, key):
        return self.data.__getitem__(key)

    def __hash__(self):
        return self.data.__hash__()

    def __iter__(self):
        return self.data.__iter__()

    def __len__(self):
        return self.data.__len__()

    def __ne__(self, other):
        return self.data.__ne__(self._cast(other))

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self.data.__repr__())

    __str__ = __repr__

    def __setitem__(self, key, value):
        self.mutated()
        return self.data.__setitem__(key, value)

    def clear(self):
        self.mutated()
        return self.data.clear()

    def copy(self):
        return type(self)(self)

    def get(self, *args):
        return self.data.get(*args)

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def pop(self, key):
        self.mutated()
        return self.data.pop(key)

    def popitem(self):
        self.mutated()
        return self.data.popitem()

    def setdefault(self, key, value):
        self.mutated()
        return self.data.setdefault(key, value)

    def update(self, mapping):
        self.mutated()
        return self.data.update(mapping)

    def values(self):
        return self.data.values()

    def mutated(self): #pragma no cover
        pass

    def _cast(self, other):
        if isinstance(other, DictWrapper):
            other = other.data
        return other


class ListWrapper(object):

    def __init__(self, *args):
        self.data = list(*args)

    def __contains__(self, index):
        return self.data.__contains__(index)

    def __delitem__(self, index):
        self.mutated()
        return self.data.__delitem__(index)

    def __delslice__(self, start, end):
        self.mutated()
        return self.data.__delslice__(start, end)

    def __eq__(self, other):
        return self.data.__eq__(other)

    def __getitem__(self, index):
        return self.data.__getitem__(index)

    def __getslice__(self, start, end):
        return self.data.__getslice__(start, end)

    def __hash__(self):
        return self.data.__hash__()

    def __iadd__(self, other):
        return type(self)(self.data.__iadd__(other))

    def __imul__(self, other):
        return type(self)(self.data.__imul__(other))

    def __iter__(self):
        return self.data.__iter__()

    def __len__(self):
        return self.data.__len__()

    def __mul__(self, other):
        return self.data.__mul__(other)

    def __ne__(self, other):
        return self.data.__ne__(other)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self.data.__repr__())

    __str__ = __repr__

    def __rmul__(self, other):
        return self.data.__rmul__(other)

    def __setitem__(self, index, value):
        self.mutated()
        return self.data.__setitem__(index, value)

    def __setslice__(self, start, end, seq):
        self.mutated()
        return self.data.__setslice__(start, end, seq)

    def append(self, value):
        self.mutated()
        return self.data.append(value)

    def count(self, value):
        return self.data.count(value)

    def extend(self, seq):
        self.mutated()
        return self.data.extend(seq)

    def index(self, value):
        return self.data.index(value)

    def insert(self, index, value):
        self.mutated()
        return self.data.insert(index, value)

    def pop(self, index):
        self.mutated()
        return self.data.pop(index)

    def remove(self, value):
        self.mutated()
        return self.data.remove(value)

    def reverse(self):
        self.mutated()
        return self.data.reverse()

    def sort(self, *args, **kw):
        self.mutated()
        return self.data.sort(*args, **kw)

    def mutated(self): #pragma no cover
        pass
