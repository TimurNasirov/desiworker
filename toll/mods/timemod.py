"""Mod that helps work with time"""
from datetime import datetime as dt
from datetime import timedelta
from time import sleep, time
from calendar import monthrange

from pytz import timezone
from log import Log

texas_tz = timezone('US/Central')

logdata = Log('rentacar.mods/timemod.py')
print = logdata.print

def time_is(time: str):
    """Returns True if time is in the current time.

    Args:
        time (str): time

    Returns:
        bool: return data
    """
    return dt.now().strftime('%H:%M') == time

def wait():
    """Wait for a given 60 - bit amount of 60 seconds"""
    sleep(60)

def timeit(func):
    """Decorator to time it took to run a function

    Args:
        func (Function): function
    """
    def wrapper(*args, **kwargs):
        a = time()
        func(*args, **kwargs)
        b = time()
        print(f'Time: {round(b - a, 3)} seconds (function: {func.__name__}).')
    return wrapper

def to_mime_format(date: dt):
    """Converts a date to a MIME format

    Args:
        date (dt): datetime

    Returns:
        str: date in MIME format
    """
    return date.strftime('%m.%Y')

def get_last_day():
    """Get the last day of the current month

    Returns:
        [type]: [description]
    """
    now = dt.now()
    return monthrange(now.year, now.month)[1]
