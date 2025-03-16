'''
CHANGE OIL
If car odometer more than oil change end, this program will create change oil task for this car and send sms to renter about he
need to change oil in the car.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all cars, changeoil_last_update will update to current time.

Collection: cars
Group: rentacar
Launch time: 11:57 [rentacar]
Marks: last-update, sms
'''

from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
from random import randint
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db, get_contract
from rentacar.mods.sms import send_sms, add_inbox, CHANGE_OIL_TEXT
from rentacar.str_config import CHANGE_OIL_TASK_COMMENT, CHANGE_OIL_NAME_TASK, USER, CHANGE_OIL_IMAGE

logdata = Log('changeoil.py')
print = logdata.print

def start_changeoil(db: client):
    """Start changeoil

    Args:
        db (client): satabase
    """
    print('start changeoil.')
    cars: list[dict] = to_dict_all(db.collection('cars').get())

    # filtering cars
    for car in cars.copy():
        if has_key(car, 'Oil_changeEnd'):
            if car['odometer'] < car['Oil_changeEnd'] or car['Oil_changeEnd'] == 0:
                cars.remove(car)
        else:
            cars.remove(car)

    tasks: list[dict] = to_dict_all(db.collection('Task').get())
    #remove tasks
    for task in tasks.copy():
        if not has_key(task, 'post'):
            if not task['status']:
                tasks.remove(task)
        else:
            if not task['post'] and not task['status']:
                tasks.remove(task)

    for car in cars.copy():
        # "for" loop in 1 line: https://python-scripts.com/for-in-one-line
        # check if car where its nickname in tasks thats name_task is "Change oil"
        if car['nickname'] in [task['nickname'] for task in tasks if task['name_task'] == 'Change oil']:
            cars.remove(car)

    for car in cars:
        create_task(db, car)

    print(f'total changeoil cars: {len(cars)}')

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'changeoil_update': dt.now(texas_tz)})
    else:
        print('changeoil last update not updated because of "--read-only" flag.')
    print('set last changeoil update.')

def create_task(db: client, car: dict):
    """Create task from the given dictionary

    Args:
        db (client): database
        car (dict): car data
    """
    print(f'write changeoil - nickname: {car["nickname"]}')
    contract = get_contract(db, car['nickname'])
    if '--read-only' not in argv:
        db.collection('Task').add({
            'id': randint(0, 10000),
            'comment': CHANGE_OIL_TASK_COMMENT.replace('{odometer}', car['odometer']).replace('{changeoil_end}', car['Oil_changeEnd']),
            'name_task': CHANGE_OIL_NAME_TASK,
            'nickname': car['nickname'],
            'date': dt.now(texas_tz),
            'photo_task': [CHANGE_OIL_IMAGE],
            'status': True,
            'post': False,
            'user': USER,
            'ContractName': contract['ContractName']
        })

    else:
        print('task not created because of "--read-only" flag.')

    if has_key(contract, 'renternumber') and '--read-only' not in argv:
        send_sms(contract['renternumber'][0], CHANGE_OIL_TEXT)
        if has_key(contract, 'renter'):
            add_inbox(db, contract['renternumber'][0], CHANGE_OIL_TEXT, contract['ContractName'], contract['renter'])
        else:
            add_inbox(db, contract['renternumber'][0], CHANGE_OIL_TEXT, contract['ContractName'], None)
    else:
        if '--read-only' in argv:
            print('sms not sent because of "--read-only" flag.')

def check_changeoil(last_update_data: dict, db: client, log: bool = False):
    """check the changeoil last update

    Args:
        last_update_data (dict): last update
        db (client): database
        log (bool, optional): show logs. Defaults to False.
    """
    if log:
        print('check changeoil last update.')
    if last_update_data['changeoil_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('changeoil has not been started for a long time: starting...')
        start_changeoil(db)
    else:
        if log:
            print('changeoil was started recently. All is ok.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess changeoil.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start change oil).')
        print('--check: check change oil last update.')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --changeoil-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('CHANGE OIL')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_changeoil(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_changeoil(last_update_data, db, True)

    print('changeoil subprocess stopped successfully.')
