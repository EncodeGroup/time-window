import unittest

from time_window.helpers import make_sequence, gaps_iterator


class TestHelpers(unittest.TestCase):

    def test_make_sequence(self):
        mylist = [1, 2]
        self.assertListEqual(mylist, make_sequence(mylist))

        myset = {1, 2}
        self.assertSetEqual(myset, make_sequence(myset))

        mytuple = (1, 2)
        self.assertTupleEqual(mytuple, make_sequence(mytuple))

        self.assertListEqual([], make_sequence(None))

        self.assertListEqual([1], make_sequence(1))

    def test_gaps_iterator(self):
        # A complete list
        a = [4, 6, 2, 'a', '6']
        a_gaps = [(4, 6), (6, 2), (2, 'a'), ('a', '6')]
        self.assertEqual(a_gaps, [i for i in gaps_iterator(a)])

        # One object list
        a = [1]
        self.assertEqual([], [i for i in gaps_iterator(a)])

        # Empty list
        a = []
        self.assertEqual([], [i for i in gaps_iterator(a)])
