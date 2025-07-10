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


from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, time
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db, get_contract
from rentacar.mods.twiliosms import send_sms, add_inbox, REGISTRATION_TEXT, sms_block_check
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
