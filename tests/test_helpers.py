import math
import time
import unittest
from datetime import datetime, timedelta

from dateutil.tz import tzutc, tzlocal

from time_window import TimeWindow
from time_window.helpers import (
    ExpirableObject, make_sequence, gaps_iterator, floor_seconds,
    utcfromtimestamp_tzaware, utcdatetime_tzaware, utc_from_local_date_parse,
    utc_date_parse
)


class TestFunctions(unittest.TestCase):

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

    def helper_time_periods_to_time_window_list(self, periods):
        return [
            TimeWindow(*list(map(utcfromtimestamp_tzaware, period)))
            for period in periods
        ]

    def test_floor_seconds(self):
        examples = [
            [datetime(2014, 10, 22, 5, 40, 0),
             datetime(2014, 10, 22, 5, 40, 0)],

            [datetime(2014, 10, 22, 5, 40, 59),
             datetime(2014, 10, 22, 5, 40, 59)],

            [datetime(2014, 10, 22, 5, 40, 59, 34),
             datetime(2014, 10, 22, 5, 40, 59)]
        ]
        for example in examples:
            self.assertEqual(floor_seconds(example[0]),
                             floor_seconds(example[1]))

    def test_utc_date_parse(self):
        date_text_samples = [
            '2015-06-10 10:00',
            '2015-01-01T12:31:23'
        ]
        for sample in date_text_samples:
            parsed_date = utc_date_parse(sample)
            self.assertIsInstance(parsed_date, datetime)
            self.assertIsInstance(parsed_date.tzinfo, tzutc)
        parsed_date = utc_date_parse(date_text_samples[0])
        self.assertTupleEqual(
            tuple(parsed_date.timetuple())[:6],
            (2015, 6, 10, 10, 0, 0)
        )
        parsed_date = utc_date_parse(date_text_samples[1])
        self.assertTupleEqual(
            tuple(parsed_date.timetuple())[:6],
            (2015, 1, 1, 12, 31, 23)
        )

    def test_utc_from_local_date_parse(self):

        now = datetime.now().replace(tzinfo=tzlocal())

        # Get the string representation
        text_date = now.__str__()
        parsed_date_utc = utc_from_local_date_parse(text_date)

        self.assertIsInstance(parsed_date_utc.tzinfo, tzutc)
        self.assertEqual(now, parsed_date_utc)

    def test_utcdatetime_tzaware(self):
        now = datetime.now()

        utc_now = utcdatetime_tzaware(
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second,
            now.microsecond,
            tzinfo=now.tzinfo
        )
        self.assertIsNone(now.tzinfo)
        self.assertIsInstance(utc_now.tzinfo, tzutc)
        self.assertEqual(now.date(), utc_now.date())
        self.assertEqual(now.time(), utc_now.time())


class TestExpirableObject(unittest.TestCase):

    def test_constructor(self):

        o = ExpirableObject()
        self.assertTrue(math.isnan(o.ttl))
        self.assertIsNone(o.expires_at)
        self.assertIsNone(o.last_updated_at)
        self.assertTrue(o.is_expired())

    def test_scenario(self):
        o = ExpirableObject()

        # Set a high ttl
        o.ttl = 35
        self.assertAlmostEqual(o.ttl, 35, delta=0.5)
        self.assertIsNotNone(o.expires_at)
        self.assertIsNotNone(o.last_updated_at)
        self.assertEqual(o.expires_at - o.last_updated_at,
                         timedelta(seconds=35))
        self.assertFalse(o.is_expired())

        # Change ttl
        o.ttl = 15
        self.assertAlmostEqual(o.ttl, 15, delta=0.5)
        self.assertIsNotNone(o.expires_at)
        self.assertIsNotNone(o.last_updated_at)
        self.assertEqual(o.expires_at - o.last_updated_at,
                         timedelta(seconds=15))
        self.assertFalse(o.is_expired())

        # Set a small ttl
        o.ttl = 1
        self.assertAlmostEqual(o.ttl, 1, delta=0.5)
        self.assertIsNotNone(o.expires_at)
        self.assertIsNotNone(o.last_updated_at)
        self.assertEqual(o.expires_at - o.last_updated_at,
                         timedelta(seconds=1))
        self.assertFalse(o.is_expired())

        # Expire ttl
        time.sleep(1)
        self.assertLess(o.ttl, 0)
        self.assertIsNotNone(o.expires_at)
        self.assertIsNotNone(o.last_updated_at)
        self.assertEqual(o.expires_at - o.last_updated_at,
                         timedelta(seconds=1))
        self.assertTrue(o.is_expired())

        # Reset to a new ttl
        o.ttl = 10
        self.assertAlmostEqual(o.ttl, 10, delta=0.5)
        self.assertIsNotNone(o.expires_at)
        self.assertIsNotNone(o.last_updated_at)
        self.assertEqual(o.expires_at - o.last_updated_at,
                         timedelta(seconds=10))
        self.assertFalse(o.is_expired())
