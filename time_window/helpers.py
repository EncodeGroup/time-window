import math
from calendar import timegm
from datetime import datetime, timedelta

from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzutc


def make_sequence(elements):
    """
    Ensure that elements is a type of sequence, otherwise
    it converts it to a list with only one element.
    """
    if isinstance(elements, (list, set, tuple)):
        return elements
    elif elements is None:
        return []
    else:
        return [elements]


def gaps_iterator(seq):
    """
    Iterate on the gaps between elements of the sequence. Each time a new item
    is requested a tuple with the next two sequential elements is returned.

    Example:
     [3,4,5,6] -> [(3,4), (4,5), (5,6)]
    """
    it = iter(seq)
    try:
        previous = next(it)
    except StopIteration:
        return

    while True:
        try:
            current = next(it)
            yield (previous, current)
            previous = current
        except StopIteration:
            return


def utctimestamp_tzaware(dt):
    """
    Get a float representing the epoch time from a datetime object in UTC
    timezone.
    :param datetime dt: A datetime (timezone-aware) object
    """
    return float(timegm(dt.timetuple()))


def utcnow_tzaware():
    """
    Get a datetime timezone-aware object of the current time in UTC zone
    """
    return datetime.now(tzutc())


def utcfromtimestamp_tzaware(timestamp):
    """
    Get datetime (timezone-aware) object in UTC timezone from timestamp.
    :param float timestamp: A float representing time in epoch timestamp.
    """
    return datetime.fromtimestamp(timestamp, tz=tzutc())


def floor_seconds(dt):
    """
    Return a copy of a datetime object that does not include
    any division of seconds
    :param datetime dt: The datetime to round down.
    """
    return dt - timedelta(microseconds=dt.microsecond)


def utc_date_parse(text):
    """
    Convert a valid datetime text representation
    to a timezone-aware UTC datetime object

    :param unicode text: formatted datetime text
    :rtype: datetime
    """
    from dateutil.tz import tzutc
    dt = dateutil_parse(text)
    return dt.replace(tzinfo=tzutc())


def utc_from_local_date_parse(text):
    """
    Convert a valid datetime text representation given in local timezone
    to a timezone-aware datetime object in UTC timezone

    :param unicode text: formatted datetime text
    :rtype: datetime
    """
    from dateutil.tz import tzlocal, tzutc
    dt_local = dateutil_parse(text).replace(tzinfo=tzlocal())
    return dt_local.astimezone(tzutc())


def utcdatetime_tzaware(*args, **kwargs):
    """
    Get datetime (timezone-aware) object in UTC timezone
    :param args: Same as for datetime.datetime objects
    :return: A timezone-aware datetime object
    :rtype: datetime
    """
    kwargs['tzinfo'] = tzutc()
    return datetime(*args, **kwargs)


class ExpirableObject(object):
    """
    Generic class for implementing an expirable process.

    Attributes:
        ttl             -- If you set this property then it will start
                           counting down till it expires
                           Retrieving this property you can check how
                           much time (in seconds) is left till expires.

        expires_at      -- Get the timestamp that this object will expire.
        last_updated_at -- Get the timestamp that this object was updated.
    """
    def __init__(self):
        """
        The object is initialized in expired mode
        """
        super(ExpirableObject, self).__init__()
        self.expires_at = None
        self.last_updated_at = None

    @property
    def ttl(self):
        """
        Get the current time-to-live of the object
        """
        if self.expires_at is None:
            return float('nan')
        return (self.expires_at - utcnow_tzaware()).total_seconds()

    @ttl.setter
    def ttl(self, ttl):
        """
        Refresh the object and a new expiration time-to-live
        :param int ttl: The time-to-live in seconds
        """
        self.last_updated_at = utcnow_tzaware()
        self.expires_at = \
            self.last_updated_at + timedelta(seconds=ttl)

    def is_expired(self):
        """
        Check if the object has expired (ttl < 0 or uninitialized)
        :rtype: boolean
        """
        return math.isnan(self.ttl) or self.ttl < 0
