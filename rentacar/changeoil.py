"""
changeoil.py
============

This script helps track and remind when cars in the rental fleet need an oil change.

Functions
---------
• **Finds cars that need an oil change**
  - Checks the cars collection and keeps only those where the odometer
    has reached the oil change limit.

• **Avoids duplicates**
  - Looks into the Task collection to make sure no existing "Change oil" task
    is already active for the same car.

• **Creates new tasks**
  - For each car that needs an oil change, it creates a task with:
    - A comment that includes current mileage
    - A default oil change image
    - Contract name (if available)

• **Sends a text message (SMS) to the renter**
  - If the car is currently rented and SMS sending is not blocked,
    it sends a reminder using the preset `CHANGE_OIL_TEXT`.

• **Logs the update time**
  - Saves the date and time when the script was last run so it won’t repeat too often.

Flags
-----
`--read-only`
    Run in test mode. No tasks are added, and no SMS messages are sent.

`--no-sms`
    Disables SMS notifications, but still creates tasks in the system.

linting: 9.8
"""


from sys import argv
from random import randint

from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, time
from rentacar.mods.firemod import to_dict_all, has_key, get_contract, FieldFilter, Or, And
from rentacar.mods.twiliosms import send_sms, add_inbox, CHANGE_OIL_TEXT, sms_block_check

logdata = Log('changeoil.py')
print = logdata.print
IMAGE = "https://firebasestorage.googleapis.com/v0/b/rentacar-qmt96z.appspot.com/o/oil-change-icon\
10%20(1).jpg?alt=media&token=9387ed74-f0ae-4908-9a25-82254f269c79"
def start_changeoil(db) -> None:
    """Runs the full process of checking, filtering, and creating oil change tasks."""
    print('start changeoil.')
    start_time = time()
    cars: list[dict] = to_dict_all(db.collection('cars')
        .where(filter=FieldFilter('Oil_changeEnd', '!=', 0)).get())
    reads = len(cars)

    # filtering cars
    for car in cars.copy():
        if car['odometer'] < car['Oil_changeEnd']:
            cars.remove(car)

    tasks: list[dict] = to_dict_all(db.collection('Task')
        .where(filter=FieldFilter('name_task', '==', 'Change oil'))
        .where(filter=Or([
            FieldFilter('status', '==', True),
            And([
                FieldFilter('status', '==', False),
                FieldFilter('post', '==', True)
            ])
        ])).get())
    reads += len(tasks)

    for car in cars.copy():
        # check if car where its nickname in tasks
        if car['nickname'] in [task['nickname'] for task in tasks]:
            cars.remove(car)

    for car in cars:
        create_task(db, car)

    print(
        f'total changeoil cars: {len(cars)}. Time: {round(time() - start_time, 2)}.'
        f' Reads: {reads}'
    )

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update')\
            .update({'changeoil_update': dt.now(texas_tz)})
    else:
        print('changeoil last update not updated because of "--read-only" flag.')
    print('set last changeoil update.')

def create_task(db, car: dict) -> None:
    """Creates a task for a single car and optionally sends an SMS."""
    print(f'write changeoil - nickname: {car["nickname"]}')
    contract = get_contract(db, car['nickname'])
    if '--read-only' not in argv:
        db.collection('Task').add({
            'id': randint(0, 10000),
            'comment': f'Change oil, current odometer: {car['odometer']} ({car['Oil_changeEnd']})',
            'name_task': 'Change oil',
            'nickname': car['nickname'],
            'date': dt.now(texas_tz),
            'photo_task': [IMAGE],
            'status': True,
            'post': False,
            'user': 'python',
            'ContractName': contract['ContractName']
        })

    else:
        print('task not created because of "--read-only" flag.')

    if has_key(contract, 'renternumber') and '--read-only' not in argv:
        if sms_block_check(contract):
            if send_sms(contract['renternumber'][0], CHANGE_OIL_TEXT):
                if has_key(contract, 'renter'):
                    add_inbox(db, contract['renternumber'][0], CHANGE_OIL_TEXT,
                        contract['ContractName'], contract['renter'])
                else:
                    add_inbox(db, contract['renternumber'][0], CHANGE_OIL_TEXT,
                        contract['ContractName'], None)
    else:
        if '--read-only' in argv:
            print('sms not sent because of "--read-only" flag.')

def check_changeoil(last_update_data: dict, db, log: bool = False) -> None:
    """Checks if more than 24 hours have passed since the last run, and if so, starts the process.
    """
    if log:
        print('check changeoil last update.')
    if last_update_data['changeoil_update']\
        .astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('changeoil has not been started for a long time: starting...')
        start_changeoil(db)
    else:
        if log:
            print('changeoil was started recently. All is ok.')
