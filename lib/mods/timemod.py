from datetime import datetime as dt
from time import sleep, time
from lib.log import Log
from datetime import timedelta
from pytz import timezone
texas_tz = timezone('US/Central')

logdata = Log('mods/timemod.py')
print = logdata.print

def time_is(time):
    return dt.now().strftime('%H:%M') == time

def wait():
    sleep(60)

def timeit(func):
    def wrapper(*args, **kwargs):
        a = time()
        func(*args, **kwargs)
        b = time()
        print(f'Time: {round(b - a, 3)} seconds (function: {func.__name__}).')
    return wrapper

def now_with_payday(payday: dt):
    return dt.now(texas_tz).replace(day=int(payday.strftime('%#d')))

def to_MY_format(date: dt):
    return date.strftime('%m.%Y')