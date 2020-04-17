from datetime import datetime, timedelta

from babel.dates import format_timedelta
from dateutil.relativedelta import relativedelta

from time_window.helpers import (
    make_sequence, utcfromtimestamp_tzaware, utctimestamp_tzaware
)


def _sort_time_windows_since(tw1, tw2):
    """
    Sort ascending two time windows based on their since values
    :param TimeWindow tw1: One of two time windows
    :param TimeWindow  tw2: One of two time windows
    :return: A list with sorted time windows
    :rtype: list(TimeWindow)
    """
    if tw1.since < tw2.since:
        return [tw1, tw2]
    else:
        return [tw2, tw1]


def _get_first_day_of_next_month(dt):
    """
    Get the first day of next month for the given datetime object
    :param datetime dt: The datetime object to calculate the first day
        of next month
    :return: The first day of the next month
    :rtype: datetime
    """
    next_month = dt + relativedelta(months=1)
    next_month = next_month.replace(day=1)

    return datetime.combine(next_month, datetime.min.time())


class TimeWindow(object):
    """
    Representation of range in time space. The object represents all possible
    timestamps in range [since, until). Apart from representation TimeWindow
    provides a limited support for set operators like union, intersection,
    complement.

    Attributes:
        since    The lower (closed) boundary of this range
        until    The upper (open) boundary of this range
        delta    The distance between upper and lower boundaries.
    """

    def __init__(self, tm_since, tm_until):
        """
        Initialize a new TimeWindow object

        :param datetime tm_since: The lower (closed) boundary of this time
        window.
        :param datetime tm_until: The upper (open) boundary of this time window
        """
        if not isinstance(tm_since, datetime):
            raise TypeError('"since" must be of datetime.datetime type')
        if not isinstance(tm_until, datetime):
            raise TypeError('"until" must be of datetime.datetime type')
        if not tm_until >= tm_since:
            raise ValueError('"until" cannot be earlier of "since"')
        self.since = tm_since
        self.until = tm_until

    @classmethod
    def from_timedelta(cls, tm, delta):
        """
        Create a new time window based on a time stamp and a time delta.
        :param datetime tm: The one boundary of the time stamp
        :param timedelta delta: The distance to the other boundary (positive
        or negative)
        """
        assert isinstance(tm, datetime)
        assert isinstance(delta, timedelta)
        boundaries = sorted([tm, tm + delta])

        return cls(boundaries[0], boundaries[1])

    @classmethod
    def smallest_possible(cls, time_windows):
        """
        Get the smallest possible TimeWindow object that can contain
        a list of other TimeWindow objects.

        :param list[TimeWindow] time_windows: A sequence of TimeWindow objects
        :rtype: TimeWindow
        """
        since = min([tw.since for tw in time_windows])
        until = max([tw.until for tw in time_windows])
        return cls(since, until)

    @property
    def delta(self):
        """
        Get the delta (size) of this window.
        :rtype: timedelta
        """
        return self.until - self.since

    @property
    def middle(self):
        """
        Get the time that is in the middle of this window.
        :rtype: datetime
        """
        return self.since + self.delta/2

    def overlaps(self, other):
        """
        Check if this object overlaps with another TimeWindow object.

        :return: Returns True if there is an overlapping or False.
        :rtype: bool
        """
        since = max(self.since, other.since)
        until = min(self.until, other.until)
        if since >= until:
            return False
        return True

    def contiguous(self, other):
        """
        Check if this object is contiguous with another TimeWindow object.
        Contiguous are considered objects that do not overlap and share
        one boundary.
        :param TimeWindow other: The other part of this operation
        :rtype: False|list[TimeWindow]
        :return: In case that these two objects are not contiguous it will
        return False.
        Else it will return a list of these two objects ordered as earliest
        first. The common boundary is the end of the first and the start of
        the second object in the list.

        """
        if not self.overlaps(other):
            tws = _sort_time_windows_since(self, other)
            if tws[0].until == tws[1].since:
                return tws
        return False

    def contains(self, other):
        """
        Check if this object contains (completely) another TimeWindow object
        or a specific time stamp.

        Using "in" operator produces the same result.
        :param TimeWindow other: The other part of this operation
        :rtype: bool
        """
        if isinstance(other, datetime):
            return self.since <= other < self.until
        elif isinstance(other, TimeWindow):
            return self.since <= other.since \
                   and self.until >= other.until
        raise TypeError("Operator 'in' for {0} is undefined"
                        .format(other))
    __contains__ = contains

    def union(self, other):
        """
        Calculate the union between this and another TimeWindow object.
        Depending the argument values, this operation may return a new
        TimeWindow object or a list of non-overlapping TimeWindow objects.
        In the case of list, objects are sorted as earliest first.

        Using | operator produces the same result.
        :param TimeWindow other: The other part of this operation
        :rtype: TimeWindow|list[TimeWindow]
        """
        if not self.overlaps(other):
            tws = _sort_time_windows_since(self, other)
            if tws[0].until == tws[1].since:
                return TimeWindow(tws[0].since, tws[1].until)
            else:
                return tws
        since = min(self.since, other.since)
        until = max(self.until, other.until)
        return TimeWindow(since, until)
    __or__ = union

    def intersection(self, other):
        """
        Calculate the intersection between two time windows. If there is no
        intersection it will return None otherwise a TimeWindow object.

        Using & operator produces the same result.
        :param TimeWindow other: The other part of this operation
        :rtype None|TimeWindow
        """
        since = max(self.since, other.since)
        until = min(self.until, other.until)
        if since >= until:
            return None
        return TimeWindow(since, until)
    __and__ = intersection

    def complement(self, other):
        """
        Calculate the complement between this and another TimeWindow object.

        Returns None if the result of this operation is an empty range. In
        other cases it will return a TimeWindow object if the range is
        contiguous or a list of TimeWindow objects ordered as earliest first.

        Using self - other produces the same result.
        :param TimeWindow other: The other part of this operation
        :rtype: TimeWindow|list[TimeWindow]|None
        """

        overlap = self & other
        if overlap is None:
            # No overlapping, means we return same object
            return TimeWindow(self.since, self.until)
        elif overlap == self:
            # If we have complete overlapping, nothing is left back
            return None
        elif overlap.since == self.since:
            # subtrahend is subset that have common start
            return TimeWindow(overlap.until, self.until)
        elif overlap.until == self.until:
            # subtrahend is subset that have common end
            return TimeWindow(self.since, overlap.since)
        else:
            # subtrahend is subset with no common boundaries
            return [TimeWindow(self.since, other.since),
                    TimeWindow(other.until, self.until)
                    ]
    __sub__ = complement

    def split(self, max_delta):
        """
        Split time window to a list of fixed-delta contiguous time windows that
        overlap exactly as the former time window. All new time windows will
        have a fixed delta except the last one.

        :param timedelta max_delta: A timedelta object with the delta of the
        new windows.
        :rtype: list[TimeWindow]

        """
        assert isinstance(max_delta, timedelta)
        chunks = []
        chunk_since = self.since
        while chunk_since < self.until:
            chunk_delta = min(max_delta, self.until - chunk_since)
            chunks.append(TimeWindow.from_timedelta(chunk_since, chunk_delta))
            chunk_since += chunk_delta
        return chunks

    def split_per_day(self):
        """
        Split time window to a list of time windows that are contiguous have
        100% overlapping with this one and the section has been performed
        on each change of day.
        """
        day_periods = []
        day_delta = timedelta(days=1)
        start_time = self.since
        while True:
            end_time = (
                start_time.replace(hour=0, minute=0, second=0, microsecond=0)
                + day_delta
            )
            if end_time > self.until:
                day_periods.append(TimeWindow(start_time, self.until))
                return day_periods
            day_periods.append(TimeWindow(start_time, end_time))
            start_time = end_time

    def split_per_week(self):
        """"
        Split time window to a list of time windows that are contiguous have
        100% overlapping with this one and the section has been performed
        on each change of week.
        """
        week_periods = []
        week_delta = timedelta(days=7)
        start_time = self.since
        while True:
            beginning_of_week = start_time - timedelta(
                days=start_time.weekday()
            )
            end_of_week = beginning_of_week.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + week_delta
            if end_of_week > self.until:
                week_periods.append(TimeWindow(start_time, self.until))
                return week_periods
            week_periods.append(TimeWindow(start_time, end_of_week))
            start_time = end_of_week

    def split_per_month(self):
        """"
        Split time window to a list of time windows that are contiguous have
        100% overlapping with this one and the section has been performed
        on each change of month.
        """
        month_periods = []
        start_time = self.since
        while True:
            end_time = _get_first_day_of_next_month(start_time)
            if end_time > self.until:
                month_periods.append(TimeWindow(start_time, self.until))
                return month_periods
            month_periods.append(TimeWindow(start_time, end_time))
            start_time = end_time

    def __eq__(self, other):
        return self.since == other.since and self.until == other.until

    def __ne__(self, other):
        return self.since != other.since or self.until != other.until

    def __str__(self):
        return "period of {delta}, from {s.since} to {s.until}".format(
            delta=format_timedelta(self.delta, locale='en_US'), s=self
        )

    def __repr__(self):
        return "{cls.__name__}({since_repr}, {until_repr})" \
            .format(cls=self.__class__,
                    since_repr=repr(self.since),
                    until_repr=repr(self.until))

    def __hash__(self):
        return hash((self.since, self.until,))


class TimeWindowsCollection(object):
    """
    A collection of time windows defines can be used to define a non
    continuous time area, or a batch of time windows.
    """
    def __init__(self, time_windows, sorted_since=False):
        """
        Construct a collection from a list of time windows
        :param list[TimeWindow] time_windows: The list of time windows
        :param bool sorted_since: If true, then the list is considered sorted
        on the since key.
        """
        self.__time_windows_raw = time_windows
        if sorted_since:
            self.__time_windows_sorted_by_since = time_windows
        else:
            self.__time_windows_sorted_by_since = None
        self.__time_windows_splitted = None

    @property
    def time_windows(self):
        return self.__time_windows_raw

    @property
    def time_windows_sorted_by_since(self):
        if self.__time_windows_sorted_by_since is None:
            self.__time_windows_sorted_by_since = \
                sorted(self.__time_windows_raw,
                       key=lambda tw: tw.since)
        return self.__time_windows_sorted_by_since

    def compressed(self):
        """
        Compress the list of time windows in the smallest possible equivalent
        list of time windows that define the same time area as the former one.

        :rtype: list[TimeWindow]
        """
        time_windows = self.time_windows_sorted_by_since
        if not time_windows:
            return TimeWindowsCollection([])
        stack = []

        latest = {
            'since': None,
            'until': None
        }

        for current in time_windows:
            if latest['until'] is None:
                latest['since'] = current.since
                latest['until'] = current.until
            elif latest['until'] >= current.since:
                latest['until'] = max(latest['until'], current.until)
            else:
                stack.append(TimeWindow(latest['since'], latest['until']))
                latest['since'] = current.since
                latest['until'] = current.until

        stack.append(TimeWindow(latest['since'], latest['until']))
        return TimeWindowsCollection(stack, sorted_since=True)

    def complement(self, period):
        """
        Get the complement of this spatial time area  in a given time range.

        :param TimeWindow period: The bigger time range to get the complement
        of.
        :rtype: list[TimeWindow]
        """
        inverse = [period]
        time_windows = self.time_windows_sorted_by_since
        for tw in time_windows:
            inverse[-1:] = make_sequence(inverse[-1] - tw)
        return TimeWindowsCollection(inverse, sorted_since=True)

    def __repr__(self):
        return repr(self.time_windows)


def time_window_from_timestamps(period_as_timestamps):
    """
    Create a TimeWindow from a tuple of epoch timestamps.
    :param (int, int) period_as_timestamps: Tuple containing the start epoch
    timestamp as the first element and the end epoch timestamp as the second.
    :rtype: TimeWindow
    """
    since, until = period_as_timestamps
    return TimeWindow(
        utcfromtimestamp_tzaware(since),
        utcfromtimestamp_tzaware(until)
    )


def time_window_to_timestamps(time_window):
    """
    Convert a TimeWindow instance to a tuple of epoch timestamps.
    :param TimeWindow time_window: the time window to be converted.
    :rtype: (int, int)
    """
    return (
        utctimestamp_tzaware(time_window.since),
        utctimestamp_tzaware(time_window.until)
    )
