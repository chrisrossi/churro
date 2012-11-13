try:
    import unittest2 as unittest
    unittest # stfu pyflakes
except ImportError:
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
        self.assertEqual(root.keys(), ['a', 'b'])
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
        self.assertEqual(root.keys(), ['a', 'b'])
        self.assertEqual(list(iter(root)), ['a', 'b'])
        self.assertTrue(bool(root))
        self.assertIn('a', root)

        root['c'] = TestFolder('e', 'f')
        self.assertEqual(len(root['c']), 0)

        with self.assertRaises(KeyError):
            root['d']


class TestClass(churro.Persistent):
    one = churro.PersistentProperty()
    two = churro.PersistentProperty()

    def __init__(self, one, two):
        self.one = one
        self.two = two


class TestFolder(churro.PersistentFolder, TestClass):
    pass

