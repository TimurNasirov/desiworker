'''
INSURANCE
If renter`s insurance expired, this program will create task and send sms to renter about he need to renew insurance.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all contracts, insurance_last_update will update to current time.

Collection: Contract
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
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db
from rentacar.mods.sms import send_sms, add_inbox, INSURANCE_TEXT, sms_block_check
from rentacar.str_config import INSURANCE_TASK_COMMENT, INSURANCE_NAME_TASK, INSURANCE_IMAGE, USER

logdata = Log('insurance.py')
print = logdata.print

def start_insurance(db: client):
    """Start insurance

    Args:
        db (client): database
    """
    print('start insurance.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())

    # filtering contracts
    for contract in contracts.copy():
        if has_key(contract, 'Insurance_end'):
            if contract['Insurance_end'].astimezone(texas_tz) > dt.now(texas_tz) or not contract['Active']:
                contracts.remove(contract)
        else:
            contracts.remove(contract)

    tasks: list[dict] = to_dict_all(db.collection('Task').get())
    #remove tasks
    for task in tasks.copy():
        if not has_key(task, 'post'):
            if not task['status']:
                tasks.remove(task)
        else:
            if not task['post'] and not task['status']:
                tasks.remove(task)

    for contract in contracts.copy():
        # "for" loop in 1 line: https://python-scripts.com/for-in-one-line
        # check if contract where its nickname in tasks thats name_task is "Insurance"
        if contract['nickname'] in [task['nickname'] for task in tasks if task['name_task'] == 'Insurance']:
            contracts.remove(contract)

    for contract in contracts:
        create_task(db, contract)

    print(f'total insurance contracts: {len(contracts)}')

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'insurance_update': dt.now(texas_tz)})
    else:
        print('insurance last update not updated because of "--read-only" flag.')
    print('set last insurance update.')

def create_task(db: client, contract: dict):
    """Create a task in the database

    Args:
        db (client): database
        contract (dict): contract data
    """
    print(f'write insurance - nickname: {contract["nickname"]}')
    if '--read-only' not in argv:
        db.collection('Task').add({
            'id': randint(20000, 30000),
            'comment': INSURANCE_TASK_COMMENT,
            'name_task': INSURANCE_NAME_TASK,
            'nickname': contract['nickname'],
            'date': dt.now(texas_tz),
            'photo_task': [INSURANCE_IMAGE],
            'status': True,
            'post': False,
            'user': USER,
            'ContractName': contract['ContractName']
        })

    else:
        print('task not created because of "--read-only" flag.')

    if has_key(contract, 'renternumber') and '--read-only' not in argv:
        if sms_block_check(contract):
            send_sms(contract['renternumber'][0], INSURANCE_TEXT)
            if has_key(contract, 'renter'):
                add_inbox(db, contract['renternumber'][0], INSURANCE_TEXT, contract['ContractName'], contract['renter'])
            else:
                add_inbox(db, contract['renternumber'][0], INSURANCE_TEXT, contract['ContractName'], None)
    else:
        if '--read-only' in argv:
            print('sms not sent because of "--read-only" flag.')

def check_insurance(last_update_data: dict, db: client, log: bool = False):
    """Check if an insurance process has been updated

    Args:
        last_update_data (dict): last update
        db (client): database
        log (bool, optional): show logs. Defaults to False.
    """
    if log:
        print('check insurance last update.')
    if last_update_data['insurance_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('insurance has not been started for a long time: starting...')
        start_insurance(db)
    else:
        if log:
            print('insurance was started recently. All is ok.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess insurance.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start insurance).')
        print('--check: check insurance last update.')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --insurance-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('INSURANCE')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_insurance(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_insurance(last_update_data, db, True)

    print('insurance subprocess stopped successfully.')
