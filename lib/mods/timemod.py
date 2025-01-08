from datetime import datetime as dt
from time import sleep, time
from lib.log import Log

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