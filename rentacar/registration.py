'''
REGISTRATION
If car need registration (TO), this program will create registration task and send sms tp renter about he need to come to office and do T/O.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all cars, registration_last_update will update to current time.

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
from rentacar.mods.timemod import dt, timedelta, texas_tz, to_mime_format, time
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db, get_contract
from rentacar.mods.sms import send_sms, add_inbox, REGISTRATION_TEXT, sms_block_check
from rentacar.str_config import REGISTRATION_TASK_COMMENT, REGISTRATION_NAME_TASK, USER, REGISTRATION_IMAGE

logdata = Log('registration.py')
print = logdata.print

def start_registration(db: client):
    """Start the registration

    Args:
        db (client): database
    """
    start_time = time()
    print('start registration.')
    cars: list[dict] = to_dict_all(db.collection('cars').get())

    # filtering cars
    for car in cars.copy():
        if has_key(car, 'TO_end'):
            if car['TO_end'].astimezone(texas_tz) > dt.now(texas_tz):
                cars.remove(car)
        else:
            cars.remove(car)

    tasks: list[dict] = to_dict_all(db.collection('Task').get())
    #remove tasks
    for task in tasks.copy():
        if task['name_task'] != 'Registration' or not task['status']:
            tasks.remove(task)

    for car in cars.copy():
        # "for" loop in 1 line: https://python-scripts.com/for-in-one-line
        # check if car where its nickname in tasks thats name_task is "Registration"
        if car['nickname'] in [task['nickname'] for task in tasks]:
            cars.remove(car)

    for car in cars:
        create_task(db, car)

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'registration_update': dt.now(texas_tz)})
        print('set last registration update.')
    else:
        print('registration last update not updated because of "--read-only" flag.')
    print(f'registration work completed. Updated cars: {len(cars)}. Time: {round(time() - start_time, 2)} seconds.')


def create_task(db: client, car: dict):
    """create a task

    Args:
        db (client): database
        car (dict): car data
    """
    print(f'write registration - nickname: {car["nickname"]}')
    contract = get_contract(db, car['nickname'])
    if '--read-only' not in argv:
        db.collection('Task').add({
            'id': randint(30000, 40000),
            'comment': REGISTRATION_TASK_COMMENT,
            'name_task': REGISTRATION_NAME_TASK,
            'nickname': car['nickname'],
            'date': dt.now(texas_tz),
            'photo_task': [REGISTRATION_IMAGE],
            'status': True,
            'post': False,
            'user': USER,
            'ContractName': contract['ContractName']
        })

    else:
        print('task not created because of "--read-only" flag.')

    if has_key(contract, 'renternumber') and '--read-only' not in argv:
        if sms_block_check(contract):
            if send_sms(contract['renternumber'][0], REGISTRATION_TEXT):
                if has_key(contract, 'renter'):
                    add_inbox(db, contract['renternumber'][0], REGISTRATION_TEXT, contract['ContractName'], contract['renter'])
                else:
                    add_inbox(db, contract['renternumber'][0], REGISTRATION_TEXT, contract['ContractName'], None)
    else:
        if '--read-only' in argv:
            print('sms not sent because of "--read-only" flag.')

def check_registration(last_update_data: dict, db: client, log: bool = False):
    """Check the registration last update time

    Args:
        last_update_data (dict): last update
        db (client): database
        log (bool, optional): show log. Defaults to False.
    """
    if log:
        print('check registration last update.')
    if last_update_data['registration_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('registration has not been started for a long time: starting...')
        start_registration(db)
    else:
        if log:
            print('registration was started recently. All is ok.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess registration.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start registration).')
        print('--check: check registration last update.')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --registration-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('REGISTRATION')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_registration(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_registration(last_update_data, db, True)

    print('registration subprocess stopped successfully.')
