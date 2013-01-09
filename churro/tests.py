try:
    import unittest2 as unittest
    unittest # pragma no cover stfu pyflakes
except ImportError:  # pragma no cover
    import unittest

import churro
import transaction


class ChurroTests(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp('.churro-test')

    def tearDown(self):
        import shutil
        transaction.abort()
        shutil.rmtree(self.tmp)

    def make_one(self, **kw):
        from churro import Churro as test_class
        return test_class(self.tmp, **kw)

    def test_empty_repo(self):
        repo = self.make_one()
        folder = repo.root()
        self.assertEqual(len(folder), 0)

    def test_save_and_retrieve_one_object(self):
        repo = self.make_one()
        root = repo.root()
        self.assertEqual(repo.root(), root)
        obj = TestClass('foo', 'bar')
        root['test'] = obj
        self.assertIs(root['test'], obj)
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.one, 'foo')
        self.assertEqual(obj.two, 'bar')
        obj.two = 'dos'
        self.assertEqual(obj.two, 'dos')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.two, 'dos')

    def test_save_and_retrieve_one_object_in_a_folder(self):
        repo = self.make_one()
        root = repo.root()
        folder = TestFolder('uno', 'dos')
        self.assertEqual(len(folder), 0)
        root['folder'] = folder
        self.assertEqual(len(folder), 0)
        obj = TestClass('foo', 'bar')
        folder['test'] = obj
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        folder = root['folder']
        self.assertEqual(folder.one, 'uno')
        self.assertEqual(folder.two, 'dos')
        obj = folder['test']
        self.assertEqual(obj.one, 'foo')
        self.assertEqual(obj.two, 'bar')
        folder.one = 'un'
        obj.two = 'deux'
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        folder = root['folder']
        self.assertEqual(folder.one, 'un')
        obj = folder['test']
        self.assertEqual(obj.two, 'deux')

    def test_folder_ops(self):
        repo = self.make_one()
        root = repo.root()
        self.assertFalse(bool(root))
        root['a'] = a = TestClass('a', 'b')
        root['b'] = b = TestClass('c', 'd')

        self.assertEqual(len(root), 2)
        self.assertEqual(sorted(root.keys()), ['a', 'b'])
        self.assertEqual(list(iter(root)), ['a', 'b'])
        self.assertEqual(list(root.values()), [a, b])
        self.assertEqual(list(root.items()), [('a', a), ('b', b)])
        self.assertTrue(bool(root))
        self.assertIn('a', root)

        transaction.commit()
        repo = self.make_one()
        root = repo.root()

        self.assertEqual(len(root), 2)
        self.assertEqual(list(root.values()), [root['a'], root['b']])
        self.assertEqual(list(root.items()), [
            ('a', root['a']), ('b', root['b'])])
        self.assertEqual(sorted(root.keys()), ['a', 'b'])
        self.assertEqual(list(iter(root)), ['a', 'b'])
        self.assertTrue(bool(root))
        self.assertIn('a', root)

        root['c'] = TestFolder('e', 'f')
        self.assertEqual(len(root['c']), 0)

        with self.assertRaises(KeyError):
            root['d']

    def test_delete(self):
        repo = self.make_one()
        root = repo.root()
        root['a'] = TestClass('a', 'b')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        self.assertIn('a', root)
        del root['a']
        self.assertNotIn('a', root)
        with self.assertRaises(KeyError):
            del root['a']
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        self.assertNotIn('a', root)
        with self.assertRaises(KeyError):
            del root['a']

    def test_pop(self):
        repo = self.make_one()
        root = repo.root()
        root['a'] = TestClass('a', 'b')
        root['b'] = TestClass('c', 'd')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        self.assertIn('a', root)
        a = root['a']
        self.assertIs(root.pop('a'), a)
        self.assertNotIn('a', root)
        with self.assertRaises(KeyError):
            root.pop('a')
        self.assertEqual(root.pop('a', None), None)
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        self.assertNotIn('a', root)
        with self.assertRaises(KeyError):
            root.pop('a')
        self.assertEqual(root.pop('a', None), None)
        self.assertEqual(root.pop('b').one, 'c')

    def test_remove_folder(self):
        repo = self.make_one()
        root = repo.root()
        root['a'] = TestFolder('a', 'b')
        root['a']['b'] = TestFolder('c', 'd')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        self.assertIn('a', root)
        del root['a']
        self.assertNotIn('a', root)
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        self.assertNotIn('a', root)
        transaction.commit() # coverage

    def test_deep_structure(self):
        repo = self.make_one()
        root = repo.root()
        obj = TestClass('foo', TestClass('bar', 'baz'))
        root['uhoh'] = obj
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['uhoh']
        self.assertEqual(obj.one, 'foo')
        self.assertEqual(obj.two.one, 'bar')
        self.assertEqual(obj.two.two, 'baz')
        obj.two.one = 'bozo'
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['uhoh']
        self.assertEqual(obj.one, 'foo')
        self.assertEqual(obj.two.one, 'bozo')
        self.assertEqual(obj.two.two, 'baz')

    def test_not_serializable(self):
        repo = self.make_one()
        root = repo.root()
        obj = TestClass('foo', NotSerializable())
        root['oops'] = obj
        with self.assertRaises(ValueError):
            transaction.commit()

    def test_save_and_retrieve_one_object_with_dates(self):
        import datetime
        dob = datetime.date(1975, 7, 7)
        dtob = datetime.datetime(2010, 5, 12, 2, 42)
        repo = self.make_one()
        root = repo.root()
        self.assertEqual(repo.root(), root)
        obj = TestClassWithDateProperties(dob, dtob)
        root['test'] = obj
        self.assertIs(root['test'], obj)
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.three, dob)
        self.assertEqual(obj.four, dtob )
        obj.four = dtob = datetime.datetime(2010, 5, 15, 20, 36)
        self.assertEqual(obj.four, dtob)
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.four, dtob)
        obj.three = None
        obj.four = None
        self.assertEqual(obj.three, None)
        self.assertEqual(obj.four, None)
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.three, None)
        self.assertEqual(obj.four, None)

        with self.assertRaises(ValueError):
            obj.three = 'foo'
        with self.assertRaises(ValueError):
            obj.four = 'bar'

    def test_persistent_dict_and_list(self):
        repo = self.make_one()
        root = repo.root()
        obj = TestClass(
            churro.PersistentDict({'one': 1, 'two': 2}),
            churro.PersistentList([1, 2]))
        root['test'] = obj
        self.assertEqual(obj.one['one'], 1)
        self.assertEqual(obj.two[0], 1)
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        obj.one['one'] = 'one'
        self.assertEqual(obj.one['one'], 'one')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.one['one'], 'one')
        obj.two[0] = 'one'
        self.assertEqual(obj.two[0], 'one')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.two[0], 'one')

    def test_deep_structure_with_persistent_dict(self):
        repo = self.make_one()
        root = repo.root()
        obj = TestClass(churro.PersistentDict(), None)
        obj.one['foo'] = TestClass('bar', 'baz')
        root['test'] = obj
        self.assertEqual(obj.one['foo'].one, 'bar')
        self.assertEqual(obj.one['foo'].two, 'baz')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        obj.one['foo'].two = 'bathsalts'
        self.assertEqual(obj.one['foo'].two, 'bathsalts')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.one['foo'].two, 'bathsalts')

    def test_deep_structure_with_persistent_list(self):
        repo = self.make_one()
        root = repo.root()
        obj = TestClass(churro.PersistentList(), None)
        obj.one.append(TestClass('bar', 'baz'))
        root['test'] = obj
        self.assertEqual(obj.one[0].one, 'bar')
        self.assertEqual(obj.one[0].two, 'baz')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        obj.one[0].two = 'bathsalts'
        self.assertEqual(obj.one[0].two, 'bathsalts')
        transaction.commit()

        repo = self.make_one()
        root = repo.root()
        obj = root['test']
        self.assertEqual(obj.one[0].two, 'bathsalts')


class TestDottedNameResolver(unittest.TestCase):

    def call_fut(self, name):
        from churro import _resolve_dotted_name as fut
        return fut(name)

    def test_it(self):
        C = self.call_fut('email.message.Message')
        from email.message import Message
        self.assertEqual(C, Message)


class CollectionWrappersTestBase(unittest.TestCase):

    def assertNewEq(self, orig, one, two):
        assert one is not orig
        self.assertEqual(one, two)

    def assertMutated(self):
        self.assertTrue(self.o.has_been_mutated)

    def assertNotMutated(self):
        self.assertFalse(self.o.has_been_mutated)


class TestDictWrapper(CollectionWrappersTestBase):

    def setUp(self):
        from churro.collection_wrappers import DictWrapper
        class Derived(DictWrapper):
            has_been_mutated = False
            def mutated(self):
                self.has_been_mutated = True
        self.o = Derived({1: 2, 3: 4})

    def test__contains__(self):
        self.assertTrue(1 in self.o)
        self.assertNotMutated()

    def test__delitem__(self):
        del self.o[1]
        self.assertEqual(self.o, {3: 4})
        self.assertMutated()

    def test__getitem__(self):
        self.assertEqual(self.o[1], 2)
        self.assertNotMutated()

    def test__hash__(self):
        with self.assertRaises(TypeError):
            hash(self.o)
        self.assertNotMutated()

    def test__iter__(self):
        self.assertEqual(sorted(iter(self.o)), [1, 3])
        self.assertNotMutated()

    def test__len__(self):
        self.assertEqual(len(self.o), 2)
        self.assertNotMutated()

    def test__ne__(self):
        self.assertFalse(self.o != {1: 2, 3: 4})
        self.assertNotMutated()

    def test__repr__(self):
        self.assertEqual(repr(self.o), 'Derived({1: 2, 3: 4})')
        self.assertNotMutated()

    def test__setitem__(self):
        self.o[5] = 6
        self.assertEqual(self.o[5], 6)
        self.assertMutated()

    def test_clear(self):
        self.o.clear()
        self.assertEqual(self.o, {})
        self.assertMutated()

    def test_copy(self):
        from churro.collection_wrappers import DictWrapper
        other = self.o.copy()
        self.assertNewEq(self.o, other, self.o)
        self.assertIsInstance(other, DictWrapper)
        self.assertNotMutated()

    def test_get(self):
        self.assertEqual(self.o.get(1), 2)
        self.assertEqual(self.o.get(5), None)
        self.assertEqual(self.o.get(5, 6), 6)
        self.assertNotMutated()

    def test_items(self):
        self.assertEqual(sorted(self.o.items()), [(1, 2), (3, 4)])
        self.assertNotMutated()

    def test_keys(self):
        self.assertEqual(sorted(self.o.keys()), [1, 3])
        self.assertNotMutated()

    def test_pop(self):
        self.assertEqual(self.o.pop(1), 2)
        self.assertEqual(self.o, {3: 4})
        self.assertMutated()

    def test_popitem(self):
        self.assertEqual(self.o.popitem(), (1, 2)) # brittle!
        self.assertEqual(self.o, {3: 4})
        self.assertMutated()

    def test_setdefault(self):
        self.assertEqual(self.o.setdefault(1, 42), 2)
        self.assertEqual(self.o.setdefault(5, 6), 6)
        self.assertEqual(self.o, {1: 2, 3: 4, 5: 6})
        self.assertMutated()

    def test_update(self):
        self.o.update({3: 42, 5: 6})
        self.assertEqual(self.o, {1: 2, 3: 42, 5: 6})
        self.assertMutated()

    def test_values(self):
        self.assertEqual(sorted(self.o.values()), [2, 4])
        self.assertNotMutated()


class TestListWrapper(CollectionWrappersTestBase):

    def setUp(self):
        from churro.collection_wrappers import ListWrapper
        class Derived(ListWrapper):
            has_been_mutated = False
            def mutated(self):
                self.has_been_mutated = True
        self.o = Derived([1, 2, 3, 2, 1])

    def test__contains__(self):
        self.assertTrue(2 in self.o)
        self.assertNotMutated()

    def test__delitem__(self):
        del self.o[1]
        self.assertEqual(self.o, [1, 3, 2, 1])
        self.assertMutated()

    def test__delslice__(self):
        del self.o[1:3]
        self.assertEqual(self.o, [1, 2, 1])
        self.assertMutated()

    def test__getitem__(self):
        self.assertEqual(self.o[1], 2)
        self.assertNotMutated()

    def test__getslice__(self):
        self.assertEqual(self.o[1:3], [2, 3])
        self.assertNotMutated()

    def test__hash__(self):
        with self.assertRaises(TypeError):
            hash(self.o)
        self.assertNotMutated()

    def test__iadd__(self):
        self.o += [4, 5]
        self.assertEqual(self.o, [1, 2, 3, 2, 1, 4, 5])
        self.assertNotMutated()

    def test__imul__(self):
        self.o *= 2
        self.assertEqual(self.o, [1, 2, 3, 2, 1, 1, 2, 3, 2, 1])
        self.assertNotMutated()

    def test__iter__(self):
        self.assertEqual(list(iter(self.o)), [1, 2, 3, 2, 1])
        self.assertNotMutated()

    def test__len__(self):
        self.assertEqual(len(self.o), 5)
        self.assertNotMutated()

    def test__mul__(self):
        self.assertEqual(self.o * 2, [1, 2, 3, 2, 1, 1, 2, 3, 2, 1])
        self.assertEqual(self.o, [1, 2, 3, 2, 1])
        self.assertNotMutated()

    def test__ne__(self):
        self.assertFalse(self.o != [1, 2, 3, 2, 1])
        self.assertNotMutated()

    def test__repr__(self):
        self.assertEqual(repr(self.o), 'Derived([1, 2, 3, 2, 1])')
        self.assertNotMutated()

    def test__rmul__(self):
        self.assertEqual(2 * self.o, [1, 2, 3, 2, 1, 1, 2, 3, 2, 1])
        self.assertEqual(self.o, [1, 2, 3, 2, 1])
        self.assertNotMutated()

    def test__setitem__(self):
        self.o[2] = 6
        self.assertEqual(self.o, [1, 2, 6, 2, 1])
        self.assertMutated()

    def test__setslice__(self):
        self.o[2:4] = [7, 8, 9]
        self.assertEqual(self.o, [1, 2, 7, 8 , 9, 1])
        self.assertMutated()

    def test_append(self):
        self.o.append(6)
        self.assertEqual(self.o, [1, 2, 3, 2, 1, 6])
        self.assertMutated()

    def test_count(self):
        self.assertEqual(self.o.count(2), 2)
        self.assertNotMutated()

    def test_extend(self):
        self.o.extend([6, 7])
        self.assertEqual(self.o, [1, 2, 3, 2, 1, 6, 7])
        self.assertMutated()

    def test_index(self):
        self.assertEqual(self.o.index(3), 2)
        self.assertNotMutated()

    def test_insert(self):
        self.o.insert(0, 0)
        self.assertEqual(self.o, [0, 1, 2, 3, 2, 1])
        self.assertMutated()

    def test_pop(self):
        self.assertEqual(self.o.pop(0), 1)
        self.assertEqual(self.o, [2, 3, 2, 1])
        self.assertMutated()

    def test_remove(self):
        self.o.remove(3)
        self.assertEqual(self.o, [1, 2, 2, 1])
        self.assertMutated()

    def test_reverse(self):
        del self.o[0]
        self.o.reverse()
        self.assertEqual(self.o, [1, 2, 3, 2])
        self.assertMutated()

    def test_sort(self):
        self.o.sort()
        self.assertEqual(self.o, [1, 1, 2, 2, 3])
        self.assertMutated()


class TestClass(churro.Persistent):
    one = churro.PersistentProperty()
    two = churro.PersistentProperty()

    def __init__(self, one, two):
        self.one = one
        self.two = two


class TestClassWithDateProperties(TestClass):
    three = churro.PersistentDate()
    four = churro.PersistentDatetime()

    def __init__(self, three, four):
        self.three = three
        self.four = four


class TestFolder(churro.PersistentFolder, TestClass):
    pass


class NotSerializable(object):
    """Nuh uh, no way."""
