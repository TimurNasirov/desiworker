from .log import Log
logdata = Log('toll.py')
print = logdata.print

def start_toll(db):
    print('start toll.')

def check_toll(db):
    pass