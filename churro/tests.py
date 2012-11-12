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


class TestClass(churro.Persistent):
    one = churro.PersistentProperty()
    two = churro.PersistentProperty()

    def __init__(self, one, two):
        self.one = one
        self.two = two
