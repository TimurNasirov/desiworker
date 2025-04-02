from mods.timemod import time_is, wait
from mods.firemod import init_db, client
from toll import start_toll, check_toll
from log import Log
from sys import argv

logdata = Log('runner.py')
print = logdata.print
db: client = init_db()

def run_checking():
    last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
    print('check toll last update.')
    check_toll(last_update_data, db)

    if '-t' in argv:
        print('start immediately activate toll.')
        start_toll(db)
        quit()
    else:
        while True:
            if time_is('9:00') or time_is('14:00') or time_is('22:00'):
                start_toll(db)
            wait()
