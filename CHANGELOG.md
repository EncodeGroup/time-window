# Changelog


## [Unreleased]

### Added
- Add the `ExpirableObject` class to the `helpers` module.
- Add the functions `utctimestamp_tzaware`, `utcnow_tzaware`, `utcfromtimestamp_tzaware`, `floor_seconds`, `utc_date_parse`, `utc_from_local_date_parse`, `utcdatetime_tzaware` to the `helpers` module.
- Add dependency to the `python-dateutil` library.
- Add the functions `time_window_from_timestamps` and `time_window_to_timestamps` to the `time_window` module.
- Add the methods `split_per_week` and `split_per_month` to the `TimeWindow` class.


## [0.0.1] - 2017-06-20

The initial version of the library.

### Added
- Add the functions `make_sequence` and `gaps_iterator` in the `helpers` module.
- Add the `TimeWindow` and `TimeWindowsCollection` classes in the `time_window` module.
