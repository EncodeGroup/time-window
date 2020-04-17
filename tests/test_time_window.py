from datetime import datetime, timedelta
import unittest

from time_window.helpers import gaps_iterator, utcfromtimestamp_tzaware
from time_window import (
    TimeWindow, TimeWindowsCollection, time_window_from_timestamps,
    time_window_to_timestamps
)


class TestTimeWindow(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now()

    def tm_windows_examples(self):
        """
        Generate a set of fixed time windows with the following
        relationships between them. The actual time scale and point in time
        may vary.

        Tbase  =      |_______________|
        Tsneigh=   |__|
        Teneigh=                      |__|
        Toverl =             |_____________|
        Tsupset=    |_____________________|
        Tsubset=          |_____|
        """
        examples = {}
        now = self.now
        examples['Tbase'] = TimeWindow.from_timedelta(
            now,
            timedelta(minutes=10))
        examples['Tsneigh'] = TimeWindow.from_timedelta(
            examples['Tbase'].since,
            - timedelta(minutes=1))
        examples['Teneigh'] = TimeWindow.from_timedelta(
            examples['Tbase'].until,
            timedelta(minutes=1))
        examples['Toverl'] = TimeWindow.from_timedelta(
            examples['Tbase'].since + examples['Tbase'].delta / 2,
            examples['Tbase'].delta)
        examples['Tsupset'] = TimeWindow(
            examples['Tbase'].since - timedelta(minutes=1),
            examples['Tbase'].until + timedelta(minutes=1))
        examples['Tsubset'] = TimeWindow(
            examples['Tbase'].since + timedelta(minutes=1),
            examples['Tbase'].until - timedelta(minutes=1))
        return examples

    def test_constructor(self):
        now = datetime.now()
        until = now + timedelta(minutes=5)

        tw = TimeWindow(now, until)
        self.assertEqual(now, tw.since)
        self.assertEqual(until, tw.until)
        self.assertEqual(until, tw.until)

        with self.assertRaises(ValueError):
            # Test reverse order
            TimeWindow(until, now)

        with self.assertRaises(TypeError):
            TimeWindow("string", until)

        with self.assertRaises(TypeError):
            TimeWindow(now, "string")

    def test_property_middle(self):
        now = datetime.now()
        until = now + timedelta(minutes=10)
        tw = TimeWindow(now, until)
        self.assertEqual(
            tw.middle,
            now + timedelta(minutes=5)
        )

    def test_fromtimedelta(self):
        now = datetime.now()
        delta = timedelta(minutes=5)

        tw = TimeWindow.from_timedelta(now, delta)
        self.assertEqual(tw.since, now)
        self.assertEqual(tw.until, now + delta)
        self.assertEqual(tw.delta, delta)

        # Negative case
        tw = TimeWindow.from_timedelta(now, -delta)
        self.assertEqual(tw.since, now - delta)
        self.assertEqual(tw.until, now)
        self.assertEqual(tw.delta, delta)

    def test_smallestpossible(self):
        ex = self.tm_windows_examples()
        tests = [
            (ex['Tbase'], [ex['Tbase']]),
            (ex['Tbase'], [ex['Tbase'], ex['Tbase']]),
            (TimeWindow(ex['Tsneigh'].since, ex['Tbase'].until),
                [ex['Tbase'], ex['Tsneigh']]),
            (TimeWindow(ex['Tbase'].since, ex['Teneigh'].until,),
                [ex['Tbase'], ex['Teneigh']]),
            (TimeWindow(ex['Tsneigh'].since, ex['Teneigh'].until,),
                [ex['Tsneigh'], ex['Teneigh']]),
            (TimeWindow(ex['Tsneigh'].since, ex['Teneigh'].until,),
                [ex['Tsneigh'], ex['Tbase'], ex['Teneigh']]),
            (TimeWindow(ex['Tbase'].since, ex['Toverl'].until,),
                [ex['Toverl'], ex['Tbase']]),
            (ex['Tsupset'], [ex['Tsupset'], ex['Tbase']]),
            (ex['Tbase'], [ex['Tsubset'], ex['Tbase']]),
        ]
        for result, tw_set in tests:
            self.assertEqual(result, TimeWindow.smallest_possible(tw_set))

    def test__repr__(self):
        ex = self.tm_windows_examples()

        # check that it does not raise any exception with unicode
        str(repr(ex["Tbase"]))

        # Check that the representation can be used to re-create the same
        # exact object
        repr_str = repr(ex["Tbase"])

        import datetime  # NOQA
        recreated_object = eval(repr_str)

        self.assertEqual(recreated_object, ex['Tbase'])

    def test__str__(self):
        ex = self.tm_windows_examples()

        # check that it does not raise an exception
        ex["Tbase"].__str__()

        # Check that it can be unicoded
        str(ex["Tbase"].__str__())

    def test_equalities(self):
        examples1 = self.tm_windows_examples()
        examples2 = self.tm_windows_examples()
        # Create two independent lists of same examples and check
        # the expected comparison checks
        for example in examples1:
            for other_example in examples2:
                if example == other_example:
                    self.assertEqual(
                        examples1[example], examples2[other_example])
                    self.assertFalse(
                        examples1[example] != examples2[other_example])
                else:
                    self.assertNotEqual(
                        examples1[example], examples2[other_example])
                    self.assertFalse(
                        examples1[example] == examples2[other_example])

    def test_delta(self):
        ex = self.tm_windows_examples()
        self.assertEqual(ex['Tbase'].delta, timedelta(minutes=10))
        self.assertEqual(ex['Tsneigh'].delta, timedelta(minutes=1))
        self.assertEqual(ex['Teneigh'].delta, timedelta(minutes=1))
        self.assertEqual(ex['Toverl'].delta, timedelta(minutes=10))
        self.assertEqual(ex['Tsupset'].delta, timedelta(minutes=12))
        self.assertEqual(ex['Tsubset'].delta, timedelta(minutes=8))

    def test_contains(self):
        ex = self.tm_windows_examples()
        tests = [(True, 'Tbase', 'Tbase'),
                 (False, 'Tbase', 'Tsneigh'),
                 (False, 'Tbase', 'Teneigh'),
                 (False, 'Tbase', 'Toverl'),
                 (False, 'Tbase', 'Tsupset'),
                 (True, 'Tbase', 'Tsubset'),
                 ]
        for result, twname1, twname2 in tests:
            tw1 = ex[twname1]
            tw2 = ex[twname2]
            self.assertEqual(result, tw1.contains(tw2),
                             'Checking "{0}".contains("{1}")'
                             .format(twname1, twname2))
            self.assertEqual(result, tw2 in tw1,
                             'Checking "{0}".contains("{1}")'
                             .format(twname1, twname2))

            import time
            # Assert the wrong type condition
            with self.assertRaises(TypeError):
                tw1.contains(time.time())

        # Timestamps checking
        self.assertTrue(ex['Tbase'].contains(ex['Tbase'].since))
        self.assertTrue(ex['Tbase'].contains(ex['Tbase'].since +
                                             timedelta(minutes=5)))
        self.assertFalse(ex['Tbase'].contains(ex['Tbase'].until))

    def test_contiguous(self):
        ex = self.tm_windows_examples()
        tests = [(False, 'Tbase', 'Tbase'),
                 ([ex['Tsneigh'], ex['Tbase']], 'Tbase', 'Tsneigh'),
                 ([ex['Tbase'], ex['Teneigh']], 'Tbase', 'Teneigh'),
                 (False, 'Tbase', 'Toverl'),
                 (False, 'Tbase', 'Tsupset'),
                 (False, 'Tbase', 'Tsubset'),
                 ]

        for result, twname1, twname2 in tests:
            tw1 = ex[twname1]
            tw2 = ex[twname2]
            self.assertEqual(result, tw1.contiguous(tw2),
                             'Checking "{0}".contiguous("{1}")'
                             .format(twname1, twname2))

    def test_union(self):
        ex = self.tm_windows_examples()
        tests = [
            (ex['Tbase'], 'Tbase', 'Tbase'),
            (TimeWindow(ex['Tsneigh'].since, ex['Tbase'].until),
                'Tbase', 'Tsneigh'),
            (TimeWindow(ex['Tbase'].since, ex['Teneigh'].until, ),
                'Tbase', 'Teneigh'),
            ([ex['Tsneigh'], ex['Teneigh']], 'Tsneigh', 'Teneigh'),
            (TimeWindow(ex['Tbase'].since, ex['Toverl'].until),
                'Tbase', 'Toverl'),
            (ex['Tsupset'], 'Tbase', 'Tsupset'),
            (ex['Tbase'], 'Tbase', 'Tsubset'),
            ]

        for result, twname1, twname2 in tests:
            tw1 = ex[twname1]
            tw2 = ex[twname2]
            self.assertEqual(result, tw1.union(tw2),
                             'Checking "{0}".union("{1}")'
                             .format(twname1, twname2))
            self.assertEqual(result, tw1 | tw2,
                             'Checking "{0}".union("{1}")'
                             .format(twname1, twname2))
            self.assertEqual(result, tw2.union(tw1),
                             'Checking "{0}".union("{1}")'
                             .format(twname2, twname1))
            self.assertEqual(result, tw2 | tw1,
                             'Checking "{0}".union("{1}")'
                             .format(twname2, twname1))

    def test_intersection(self):
        ex = self.tm_windows_examples()
        tests = [
            (ex['Tbase'], 'Tbase', 'Tbase'),
            (None, 'Tbase', 'Tsneigh'),
            (None, 'Tbase', 'Teneigh'),
            (TimeWindow(ex['Toverl'].since, ex['Tbase'].until),
                'Tbase', 'Toverl'),
            (ex['Tbase'], 'Tbase', 'Tsupset'),
            (ex['Tsubset'], 'Tbase', 'Tsubset'),
            ]

        for result, twname1, twname2 in tests:
            tw1 = ex[twname1]
            tw2 = ex[twname2]
            self.assertEqual(result, tw1.intersection(tw2),
                             'Checking "{0}".intersection("{1}")'
                             .format(twname1, twname2))
            self.assertEqual(result, tw1 & tw2,
                             'Checking "{0}".intersection("{1}")'
                             .format(twname1, twname2))
            self.assertEqual(result, tw2.intersection(tw1),
                             'Checking "{0}".intersection("{1}")'
                             .format(twname2, twname1))
            self.assertEqual(result, tw2 & tw1,
                             'Checking "{0}".intersection("{1}")'
                             .format(twname2, twname1))

    def test_complement(self):
        ex = self.tm_windows_examples()
        tests = [
            (None, 'Tbase', 'Tbase'),
            (ex['Tbase'], 'Tbase', 'Tsneigh'),
            (ex['Tbase'], 'Tbase', 'Teneigh'),
            (TimeWindow(ex['Tbase'].since, ex['Toverl'].since),
                'Tbase', 'Toverl'),
            (None, 'Tbase', 'Tsupset'),
            ([TimeWindow(ex['Tbase'].since, ex['Tsubset'].since),
              TimeWindow(ex['Tsubset'].until, ex['Tbase'].until)],
             'Tbase', 'Tsubset'),
        ]

        for result, twname1, twname2 in tests:
            tw1 = ex[twname1]
            tw2 = ex[twname2]
            self.assertEqual(result, tw1.complement(tw2),
                             'Checking "{0}".complement("{1}")'
                             .format(twname1, twname2))
            self.assertEqual(result, tw1 - tw2,
                             'Checking "{0}".complement("{1}")'
                             .format(twname1, twname2))

    def test_overlaps(self):
        ex = self.tm_windows_examples()
        tests = [
            (True, 'Tbase', 'Tbase'),
            (False, 'Tbase', 'Tsneigh'),
            (False, 'Tbase', 'Teneigh'),
            (True, 'Tbase', 'Toverl'),
            (True, 'Tbase', 'Tsupset'),
            (True, 'Tbase', 'Tsubset'),
        ]
        for result, twname1, twname2 in tests:
            tw1 = ex[twname1]
            tw2 = ex[twname2]
            self.assertEqual(result, tw1.overlaps(tw2),
                             'Checking "{0}".overlaps("{1}")'
                             .format(twname1, twname2))
            self.assertEqual(result, tw2.overlaps(tw1),
                             'Checking "{0}".overlaps("{1}")'
                             .format(twname2, twname1))

    def test_split(self):
        ex = self.tm_windows_examples()
        #: :type tw: TimeWindow
        tw = ex['Tbase']

        def generic_chunk_tests(chunks, chunk_delta, total, last_delta=None):
            # Check size
            self.assertEqual(len(chunks), total)

            # Check chunk deltas
            for index, chunk in enumerate(chunks):
                #: :type chunk: TimeWindow
                if last_delta and index == total - 1:
                    self.assertEqual(last_delta, chunk.delta)
                    break
                self.assertEqual(chunk_delta, chunk.delta)

            # Check contiguouness
            for tw_prev, tw_next in gaps_iterator(chunks):
                #: :type tw_prev: TimeWindow
                #: :type tw_next: TimeWindow
                self.assertTrue(tw_prev.contiguous(tw_next))

            # Check lower and upper boundaries
            self.assertEqual(tw.since, chunks[0].since)
            self.assertEqual(tw.until, chunks[-1].until)

        td = timedelta(seconds=30)
        chunks = tw.split(td)
        generic_chunk_tests(chunks, td, 20)

        td = timedelta(seconds=39)
        chunks = tw.split(td)
        generic_chunk_tests(chunks, td, 16, last_delta=timedelta(seconds=15))

    def test_hash(self):

        hash1 = hash(TimeWindow.from_timedelta(datetime(2015, 1, 1),
                                               timedelta(seconds=1)))

        for i in range(0, 2048):
            self.assertEqual(hash(TimeWindow.from_timedelta(
                datetime(2015, 1, 1),
                timedelta(seconds=1))),
                hash1)

        self.assertNotEqual(
            hash(TimeWindow.from_timedelta(datetime(2015, 1, 1),
                                           timedelta(seconds=1))),
            hash(TimeWindow.from_timedelta(datetime(2015, 1, 1, 1),
                                           timedelta(seconds=1)))
        )

        self.assertNotEqual(
            hash(TimeWindow.from_timedelta(datetime(2015, 1, 1),
                                           timedelta(seconds=1))),
            hash(TimeWindow.from_timedelta(datetime(2015, 1, 1),
                                           timedelta(seconds=2)))
        )

    def test_split_per_day(self):

        # Single time test
        tw = TimeWindow(
            datetime(2015, 1, 1, 15, 30, 40, 54),
            datetime(2015, 1, 1, 15, 30, 40, 54),
        )
        self.assertEqual(
            tw.split_per_day(),
            [tw])

        # Single day test
        tw = TimeWindow(
            datetime(2015, 1, 1, 15, 30, 40, 54),
            datetime(2015, 1, 1, 16, 4, 3, 1),
        )
        self.assertEqual(
            tw.split_per_day(),
            [tw])

        # Span two days, with period less than 24 hours
        tw = TimeWindow(
            datetime(2015, 1, 1, 23),
            datetime(2015, 1, 2, 10)
        )
        self.assertEqual(
            tw.split_per_day(),
            [TimeWindow(datetime(2015, 1, 1, 23),
                        datetime(2015, 1, 2, 0)),
             TimeWindow(datetime(2015, 1, 2, 0),
                        datetime(2015, 1, 2, 10))
             ]
        )

        # Span two days, with period greater than 24 hours
        tw = TimeWindow(
            datetime(2015, 1, 1, 23),
            datetime(2015, 1, 2, 23, 30)
        )
        self.assertEqual(
            tw.split_per_day(),
            [TimeWindow(datetime(2015, 1, 1, 23),
                        datetime(2015, 1, 2, 0)),
             TimeWindow(datetime(2015, 1, 2, 0),
                        datetime(2015, 1, 2, 23, 30))
             ]
        )

        # A big test
        tw = TimeWindow(
            datetime(2015, 1, 1, 15, 30, 40, 54),
            datetime(2015, 2, 3, 5, 4, 3, 1),
        )

        self.assertEqual(
            tw.split_per_day(),
            [TimeWindow(datetime(2015, 1, 1, 15, 30, 40, 54),
                        datetime(2015, 1, 2, 0, 0)),
             TimeWindow(datetime(2015, 1, 2, 0, 0),
                        datetime(2015, 1, 3, 0, 0)),
             TimeWindow(datetime(2015, 1, 3, 0, 0),
                        datetime(2015, 1, 4, 0, 0)),
             TimeWindow(datetime(2015, 1, 4, 0, 0),
                        datetime(2015, 1, 5, 0, 0)),
             TimeWindow(datetime(2015, 1, 5, 0, 0),
                        datetime(2015, 1, 6, 0, 0)),
             TimeWindow(datetime(2015, 1, 6, 0, 0),
                        datetime(2015, 1, 7, 0, 0)),
             TimeWindow(datetime(2015, 1, 7, 0, 0),
                        datetime(2015, 1, 8, 0, 0)),
             TimeWindow(datetime(2015, 1, 8, 0, 0),
                        datetime(2015, 1, 9, 0, 0)),
             TimeWindow(datetime(2015, 1, 9, 0, 0),
                        datetime(2015, 1, 10, 0, 0)),
             TimeWindow(datetime(2015, 1, 10, 0, 0),
                        datetime(2015, 1, 11, 0, 0)),
             TimeWindow(datetime(2015, 1, 11, 0, 0),
                        datetime(2015, 1, 12, 0, 0)),
             TimeWindow(datetime(2015, 1, 12, 0, 0),
                        datetime(2015, 1, 13, 0, 0)),
             TimeWindow(datetime(2015, 1, 13, 0, 0),
                        datetime(2015, 1, 14, 0, 0)),
             TimeWindow(datetime(2015, 1, 14, 0, 0),
                        datetime(2015, 1, 15, 0, 0)),
             TimeWindow(datetime(2015, 1, 15, 0, 0),
                        datetime(2015, 1, 16, 0, 0)),
             TimeWindow(datetime(2015, 1, 16, 0, 0),
                        datetime(2015, 1, 17, 0, 0)),
             TimeWindow(datetime(2015, 1, 17, 0, 0),
                        datetime(2015, 1, 18, 0, 0)),
             TimeWindow(datetime(2015, 1, 18, 0, 0),
                        datetime(2015, 1, 19, 0, 0)),
             TimeWindow(datetime(2015, 1, 19, 0, 0),
                        datetime(2015, 1, 20, 0, 0)),
             TimeWindow(datetime(2015, 1, 20, 0, 0),
                        datetime(2015, 1, 21, 0, 0)),
             TimeWindow(datetime(2015, 1, 21, 0, 0),
                        datetime(2015, 1, 22, 0, 0)),
             TimeWindow(datetime(2015, 1, 22, 0, 0),
                        datetime(2015, 1, 23, 0, 0)),
             TimeWindow(datetime(2015, 1, 23, 0, 0),
                        datetime(2015, 1, 24, 0, 0)),
             TimeWindow(datetime(2015, 1, 24, 0, 0),
                        datetime(2015, 1, 25, 0, 0)),
             TimeWindow(datetime(2015, 1, 25, 0, 0),
                        datetime(2015, 1, 26, 0, 0)),
             TimeWindow(datetime(2015, 1, 26, 0, 0),
                        datetime(2015, 1, 27, 0, 0)),
             TimeWindow(datetime(2015, 1, 27, 0, 0),
                        datetime(2015, 1, 28, 0, 0)),
             TimeWindow(datetime(2015, 1, 28, 0, 0),
                        datetime(2015, 1, 29, 0, 0)),
             TimeWindow(datetime(2015, 1, 29, 0, 0),
                        datetime(2015, 1, 30, 0, 0)),
             TimeWindow(datetime(2015, 1, 30, 0, 0),
                        datetime(2015, 1, 31, 0, 0)),
             TimeWindow(datetime(2015, 1, 31, 0, 0),
                        datetime(2015, 2, 1, 0, 0)),
             TimeWindow(datetime(2015, 2, 1, 0, 0),
                        datetime(2015, 2, 2, 0, 0)),
             TimeWindow(datetime(2015, 2, 2, 0, 0),
                        datetime(2015, 2, 3, 0, 0)),
             TimeWindow(datetime(2015, 2, 3, 0, 0),
                        datetime(2015, 2, 3, 5, 4, 3, 1))])

    def test_split_per_week(self):

        # Single time test
        tw = TimeWindow(
            datetime(2015, 1, 1, 15, 30, 40, 54),
            datetime(2015, 1, 1, 15, 30, 40, 54),
        )
        self.assertEqual(
            tw.split_per_week(),
            [tw])

        # Single day test
        tw = TimeWindow(
            datetime(2015, 1, 1, 15, 30, 40, 54),
            datetime(2015, 1, 1, 16, 4, 3, 1),
        )
        self.assertEqual(
            tw.split_per_week(),
            [tw])

        # Span one week, with period less than 7 days
        tw = TimeWindow(
            datetime(2015, 1, 1, 23),
            datetime(2015, 1, 3, 10)
        )
        self.assertEqual(
            tw.split_per_week(),
            [
                TimeWindow(datetime(2015, 1, 1, 23), datetime(2015, 1, 3, 10))
            ]
        )

        # Span two weeks, with period greater than 7 days
        tw = TimeWindow(
            datetime(2015, 1, 1, 23),
            datetime(2015, 1, 11, 23, 30)
        )
        print(tw.split_per_week())
        self.assertEqual(
            tw.split_per_week(),
            [TimeWindow(datetime(2015, 1, 1, 23),
                        datetime(2015, 1, 5, 0)),
             TimeWindow(datetime(2015, 1, 5, 0),
                        datetime(2015, 1, 11, 23, 30))
             ]
        )

    def test_split_per_month(self):
        # Single time test
        tw = TimeWindow(
            datetime(2015, 1, 1, 15, 30, 40, 54),
            datetime(2015, 1, 1, 15, 30, 40, 54),
        )
        self.assertEqual(
            tw.split_per_month(),
            [tw])

        # Single day test
        tw = TimeWindow(
            datetime(2015, 1, 1, 15, 30, 40, 54),
            datetime(2015, 1, 1, 16, 4, 3, 1),
        )
        self.assertEqual(
            tw.split_per_month(),
            [tw])

        # Span one month, with period less than 30 days
        tw = TimeWindow(
            datetime(2015, 1, 1, 23),
            datetime(2015, 1, 15, 10)
        )
        self.assertEqual(
            tw.split_per_month(),
            [
                TimeWindow(datetime(2015, 1, 1, 23), datetime(2015, 1, 15, 10))
            ]
        )

        # Span two months, with period greater than 30 days
        tw = TimeWindow(
            datetime(2015, 1, 1, 23),
            datetime(2015, 2, 5, 23, 30)
        )
        self.assertEqual(
            tw.split_per_month(),
            [TimeWindow(datetime(2015, 1, 1, 23),
                        datetime(2015, 2, 1, 0, 0)),
             TimeWindow(datetime(2015, 2, 1, 0, 0),
                        datetime(2015, 2, 5, 23, 30))
             ]
        )

        # Span three months, with period greater than 30 days
        tw = TimeWindow(
            datetime(2015, 1, 1, 23),
            datetime(2015, 3, 5, 23, 30)
        )
        self.assertEqual(
            tw.split_per_month(),
            [TimeWindow(datetime(2015, 1, 1, 23),
                        datetime(2015, 2, 1, 0, 0)),
             TimeWindow(datetime(2015, 2, 1, 0, 0),
                        datetime(2015, 3, 1, 0, 0)),
             TimeWindow(datetime(2015, 3, 1, 0, 0),
                        datetime(2015, 3, 5, 23, 30))
             ]
        )

        # Span three months, with period greater than 30 days,
        # starting from the middle of the first month
        tw = TimeWindow(
            datetime(2015, 1, 15, 5),
            datetime(2015, 3, 6, 15)
        )
        self.assertEqual(
            tw.split_per_month(),
            [TimeWindow(datetime(2015, 1, 15, 5, 0),
                        datetime(2015, 2, 1, 0, 0)),
             TimeWindow(datetime(2015, 2, 1, 0, 0),
                        datetime(2015, 3, 1, 0, 0)),
             TimeWindow(datetime(2015, 3, 1, 0, 0),
                        datetime(2015, 3, 6, 15, 0))
             ]
        )

        # Span five months, with period greater than 30 days,
        # starting from the 10th day of the first month
        tw = TimeWindow(
            datetime(2015, 5, 10, 5),
            datetime(2015, 7, 23, 15)
        )
        self.assertEqual(
            tw.split_per_month(),
            [TimeWindow(datetime(2015, 5, 10, 5, 0),
                        datetime(2015, 6, 1, 0, 0)),
             TimeWindow(datetime(2015, 6, 1, 0, 0),
                        datetime(2015, 7, 1, 0, 0)),
             TimeWindow(datetime(2015, 7, 1, 0, 0),
                        datetime(2015, 7, 23, 15, 0))
             ]
        )

        # Span two months, with period less than 30 days,
        # starting from December
        tw = TimeWindow(
            datetime(2015, 12, 15, 5),
            datetime(2016, 1, 6, 15)
        )
        self.assertEqual(
            tw.split_per_month(),
            [TimeWindow(datetime(2015, 12, 15, 5, 0),
                        datetime(2016, 1, 1, 0, 0)),
             TimeWindow(datetime(2016, 1, 1, 0, 0),
                        datetime(2016, 1, 6, 15, 0))
             ]
        )


class TestTimeWindowsCollection(unittest.TestCase):

    def test_compress_spatial_time_area(self):
        # Test empty list
        res = TimeWindowsCollection([]).compressed()
        self.assertEqual(res.time_windows, [])

        # Test single window
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=10)
            )
        ])
        res = tws.compressed()
        self.assertEqual(res.time_windows, tws.time_windows)

        # Test two overlapping
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=10)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 5, 0),
                timedelta(minutes=10)
            ),
        ])
        res = tws.compressed()
        self.assertEqual(res.time_windows, [
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=15)
            ),
        ])

        # Test overlapping and contiguous
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=10)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 5, 0),
                timedelta(minutes=8)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 5, 0),
                timedelta(minutes=10)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 15, 0),
                timedelta(minutes=3)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=3)
            ),
        ])
        res = tws.compressed()
        self.assertEqual(res.time_windows, [
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=18)
            ),
        ])

    def test_bug_compress_spatial_time_area(self):
        # This case was captured live on debugger.
        tws = TimeWindowsCollection([
            TimeWindow(datetime(2015, 3, 4, 16, 40, 31, 0),
                       datetime(2015, 3, 4, 16, 41, 31, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 43, 44, 0),
                       datetime(2015, 3, 4, 16, 44, 44, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 43, 57, 0),
                       datetime(2015, 3, 4, 16, 44, 57, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 44, 9, 0),
                       datetime(2015, 3, 4, 16, 45, 9, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 44, 22, 0),
                       datetime(2015, 3, 4, 16, 45, 22, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 44, 35, 0),
                       datetime(2015, 3, 4, 16, 45, 35, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 46, 23, 0),
                       datetime(2015, 3, 4, 16, 47, 23, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 46, 40, 0),
                       datetime(2015, 3, 4, 16, 47, 40, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 46, 56, 0),
                       datetime(2015, 3, 4, 16, 47, 56, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 47, 12, 0),
                       datetime(2015, 3, 4, 16, 48, 12, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 47, 28, 0),
                       datetime(2015, 3, 4, 16, 48, 28, 0)),
            TimeWindow(datetime(2015, 3, 4, 16, 47, 44, 0),
                       datetime(2015, 3, 4, 16, 48, 44, 0))
        ])
        res = tws.compressed()
        self.assertEqual(res.time_windows,
                         [TimeWindow(datetime(2015, 3, 4, 16, 40, 31),
                                     datetime(2015, 3, 4, 16, 41, 31)),
                          TimeWindow(datetime(2015, 3, 4, 16, 43, 44),
                                     datetime(2015, 3, 4, 16, 45, 35)),
                          TimeWindow(datetime(2015, 3, 4, 16, 46, 23),
                                     datetime(2015, 3, 4, 16, 48, 44))])

    def test_complement_spatial_time_area(self):
        period = TimeWindow.from_timedelta(
            datetime(2015, 2, 19, 1, 0, 0),
            timedelta(hours=1)
        )

        # Test on empty list
        res = TimeWindowsCollection([]).complement(period)
        self.assertEqual(res.time_windows, [period])

        # Test on single included time window
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 10, 0),
                timedelta(minutes=10)
            )
        ])
        res = tws.complement(period)
        self.assertEqual(res.time_windows, [
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=10)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 20, 0),
                timedelta(minutes=40)
            ),
        ])

        # Test on single boundary-snapped time window
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 0o2, 19, 1, 0, 0),
                timedelta(minutes=10)
            )
        ])

        res = tws.complement(period)
        self.assertEqual(res.time_windows, [
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 10, 0),
                timedelta(minutes=50)
            ),
        ])

        # Test on single partially included time window
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 50, 0),
                timedelta(minutes=20)
            )
        ])

        res = tws.complement(period)
        self.assertEqual(res.time_windows, [
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=50)
            ),
        ])

        # Test on multiple compressed and ordered time windows
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 0, 50, 0),
                timedelta(minutes=20)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 20, 0),
                timedelta(minutes=5)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 50, 0),
                timedelta(minutes=20)
            )
        ])
        res = tws.complement(period)
        self.assertEqual(res.time_windows, [
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 10, 0),
                timedelta(minutes=10)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 25, 0),
                timedelta(minutes=25)
            ),
        ])

        # Test on multiple non-compressed and un-ordered time windows
        tws = TimeWindowsCollection([

            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 20, 0),
                timedelta(minutes=5)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 50, 0),
                timedelta(minutes=20)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 0, 52, 0),
                timedelta(minutes=18)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 0, 52, 0),
                timedelta(minutes=8)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 0, 50, 0),
                timedelta(minutes=5)
            ),
        ])

        res = tws.complement(period)
        self.assertEqual(res.time_windows, [
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 10, 0),
                timedelta(minutes=10)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 25, 0),
                timedelta(minutes=25)
            ),
        ])

    def test__repr__(self):
        tws = TimeWindowsCollection([
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 0, 0),
                timedelta(minutes=10)
            ),
            TimeWindow.from_timedelta(
                datetime(2015, 2, 19, 1, 5, 0),
                timedelta(minutes=10)
            ),
        ])

        # check that it does not raise an exception
        print(repr(tws))

        # check that it does not raise any exception with unicode
        str(repr(tws))


class TestFunctions(unittest.TestCase):

    def test_time_window_from_timestamps(self):
        start = 1420063200
        end = start + 120
        check_tw = time_window_from_timestamps((start, end))
        tw = TimeWindow(
            utcfromtimestamp_tzaware(start),
            utcfromtimestamp_tzaware(end)
        )
        self.assertEqual(check_tw, tw)

    def test_time_window_to_timestamps(self):
        start = 1420063200
        end = start + 120
        tw = TimeWindow(
            utcfromtimestamp_tzaware(start),
            utcfromtimestamp_tzaware(end)
        )
        tw_timestamps = time_window_to_timestamps(tw)
        self.assertTupleEqual(tw_timestamps, (start, end))
