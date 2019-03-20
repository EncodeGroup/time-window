[![CircleCI](https://circleci.com/gh/EncodeGroup/time-window.svg?style=shield)](https://circleci.com/gh/EncodeGroup/time-window)

# Time Window

Time Window is a small Python library that implements a representation for a
period of time, in the form of a half-open interval `[since, until)`.

## Installation

Install using `pip` from PyPI.

```bash
pip install time-window
```

## Usage

Instantiate a new `TimeWindow` object using two `datetime.datetime` objects for
the boundaries.
```python
>>> from datetime import datetime
>>> from time_window import TimeWindow

>>> since = datetime(2019, 1, 23)
>>> until = datetime(2019, 1, 29)

>>> tw = TimeWindow(since, until)
>>> tw
TimeWindow(datetime.datetime(2019, 1, 23, 0, 0), datetime.datetime(2019, 1, 29, 0, 0))
```

Alternatively, instantiate a new `TimeWindow` object using a `datetime.datetime` object and one
`datetime.timedelta` for the definition of the boundaries.
```python
>>> from datetime import timedelta

>>> delta = timedelta(days=1)

>>> tw = TimeWindow.from_timedelta(since, delta)
>>> tw
TimeWindow(datetime.datetime(2019, 1, 23, 0, 0), datetime.datetime(2019, 1, 24, 0, 0))
```

Get the size of the window.
```python
>>> tw.delta
datetime.timedelta(1)
```

Get the time that is in the middle of the window.
```python
>>> tw.middle
datetime.datetime(2019, 1, 23, 12, 0)
```

You can also check if two `TimeWindow` objects overlap.
```python
>>> tw = TimeWindow(datetime(2019, 1, 23), datetime(2019, 1, 29))
>>> tw2 = TimeWindow(datetime(2019, 1, 27), datetime(2019, 1, 30))
>>> tw.overlaps(tw2)
True
```

Complementary to the above action, you can check if two time windows are
contiguous (i.e., adjacent, sharing one boundary).
```python
>>> tw = TimeWindow(datetime(2019, 1, 23), datetime(2019, 1, 29))
>>> tw2 = TimeWindow(datetime(2019, 1, 20), datetime(2019, 1, 23))
>>> tw.contiguous(tw2)
[TimeWindow(datetime.datetime(2019, 1, 20, 0, 0), datetime.datetime(2019, 1, 23, 0, 0)),
 TimeWindow(datetime.datetime(2019, 1, 23, 0, 0), datetime.datetime(2019, 1, 29, 0, 0))]

>>> tw3 = TimeWindow(datetime(2019, 1, 20), datetime(2019, 1, 21))
>>> tw.contiguous(tw3)
False
```

Any `TimeWindow` object offers some of the standard [set operations](https://docs.python.org/3.6/library/stdtypes.html#set).
```python
>>> tw = TimeWindow(datetime(2019, 1, 23), datetime(2019, 1, 29))
>>> tw2 = TimeWindow(datetime(2019, 1, 27), datetime(2019, 1, 30))

>>> tw.intersection(tw2)
TimeWindow(datetime.datetime(2019, 1, 27, 0, 0), datetime.datetime(2019, 1, 29, 0, 0))

>>> tw.union(tw2)
TimeWindow(datetime.datetime(2019, 1, 23, 0, 0), datetime.datetime(2019, 1, 30, 0, 0))

>>> tw.complement(tw2)
TimeWindow(datetime.datetime(2019, 1, 23, 0, 0), datetime.datetime(2019, 1, 27, 0, 0))
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
