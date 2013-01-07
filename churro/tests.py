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


class TestDottedNameResolver(unittest.TestCase):

    def call_fut(self, name):
        from churro import _resolve_dotted_name as fut
        return fut(name)

    def test_it(self):
        C = self.call_fut('email.message.Message')
        from email.message import Message
        self.assertEqual(C, Message)


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
