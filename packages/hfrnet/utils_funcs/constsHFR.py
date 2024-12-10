#!/usr/bin/env python

from datetime import datetime, timezone

"""
   Project level constants
"""

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
NCCF_FORMAT = "%Y%m%d%H%M%S"
CONFIGS_DICT = {"25hr": "25 hour", "month":"monthly", "year":"annual"}
MODES = ["25 hour", "monthly", "annual"]
HOURS_IN_DAY = 24
florida_lat = [25, 26.75]
florida_lon = [-80.75, -78.75]
NUM_DEGREES = 360
RIGHT_ANGLE = 90

#minimum dates for when to do the averages
YEAR_AVG_MIN_DATE = datetime(datetime.now(timezone.utc).year, 1, 20, 0, 0, tzinfo=timezone.utc)
MONTH_AVG_MIN_DAY = 13
