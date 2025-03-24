'''
PAY EVERY
Divided with payday, work EVERY day, and add pay to active contracts renta_price / 30. Made for transition to daily payment
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all contracts, payevery_last_update will update to current time.

Collection: Contract
Group: rentacar
Launch time: 11:57 [rentacar]
Marks: last-update, sms, limit-28-upd
'''

from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
from random import randint
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, to_mime_format, get_last_day
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db, get_car
from rentacar.mods.sms import send_sms, add_inbox, PAYDAY_TEXT
from rentacar.str_config import PAYDAY_IMAGE, PAYDAY_NAME_PAY, PAYDAY_TASK_COMMENT, USER

logdata = Log('payevery.py')
print = logdata.print

def start_payevery(db: client):
    print('start payevery.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    pays: list[dict] = to_dict_all(db.collection('Task').get())

    for pay in pays.copy():
        if not (has_key(pay, 'category') or has_key(pay, 'ContractName')):
            pays.remove(pay)

    # filtering contracts
    for contract in contracts.copy():
        if not contract['Active']:
            contracts.remove(contract)

    for contract in contracts:
        if contract['ContractName'] not in [pay['ContractName'] for pay in pays if pay['category'] == 'daily rent'] or contract['pay_day'].strftime('%d') == dt.now().strftime('%d'):
            car: dict = get_car(db, contract['nickname'])
            create_payevery(db, contract, car['odometer'])
        else:
            print(f'contract {contract["ContractName"]} skipped.')

    print(f'total payevery contracts: {len(contracts)}')

    # if '--read-only' not in argv:
    #     db.collection('Last_update_python').doc('last_update').update({'payevery_update': dt.now(texas_tz)})
    # else:
    #     print('payevery last update not updated because of "--read-only" flag.')
    # print('set last payevery update.')

def start_payevery2(db: client):
    print('start payevery (2).')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    tasks: list[dict] = to_dict_all(db.collection('Task').get())

    # filtering contracts
    for contract in contracts.copy():
        if not contract['Active']:
            contracts.remove(contract)

    for contract in contracts:
        if contract['nickname'] not in [task['nickname'] for task in tasks if task['name_task'] == 'PayDay' and task['status']] and contract['last_saldo'] < -contract['renta_price'] / 30:
            create_task(db, contract)

    print(f'total payevery (2) contracts: {len(contracts)}')

def create_task(db: client, contract: dict):
    print(f'write payevery - ContractName: {contract["ContractName"]}')
    if '--read-only' not in argv:
        db.collection('Task').add({
            'id': randint(10000, 20000),
            'comment': PAYDAY_TASK_COMMENT.replace('{payday}', contract["pay_day"].day),
            'name_task': PAYDAY_NAME_TASK,
            'nickname': contract['nickname'],
            'date': dt.now(texas_tz),
            'photo_task': [PAYDAY_IMAGE],
            'status': True,
            'post': False,
            'user': USER,
            'ContractName': contract['ContractName']
        })
    else:
        print('payevery task not created because of "--read-only" flag.')

    if has_key(contract, 'renternumber') and '--read-only' not in argv:
        send_sms(contract['renternumber'][0], PAYDAY_TEXT)
        if has_key(contract, 'renter'):
            add_inbox(db, contract['renternumber'][0], PAYDAY_TEXT, contract['ContractName'], contract['renter'])
        else:
            add_inbox(db, contract['renternumber'][0], PAYDAY_TEXT, contract['ContractName'], None)
    else:
        if '--read-only' in argv:
            print('payevery sms not sent because of "--read-only" flag.')

def create_payevery(db: client, contract: dict, odometer: int):
    """Create a payment task and add it to the database

    Args:
        db (client): database
        contract (dict): contract data
        odometer (int): current odometer
    """
    print(f'write payevery - ContractName: {contract["ContractName"]}')
    if '--read-only' not in argv:
        db.collection('Pay_contract').add({
            'nickname': contract['nickname'],
            'ContractName': contract['ContractName'],
            'date': dt.now(texas_tz),
            'sum': contract['renta_price'] / 30,
            'name_pay': PAYDAY_NAME_PAY,
            'expense': True,
            'odometer': odometer,
            'user': USER,
            'owner': True,
            'category': 'daily rent'
        })
    else:
        print('payevery pay not created because of "--read-only" flag.')


# def check_payevery(last_update_data: dict, db: client, log: bool = False):
#     """check the day of the last update

#     Args:
#         last_update_data (dict): last update
#         db (client): database
#         log (bool, optional): show logs. Defaults to False.
#     """
#     if log:
#         print('check payevery last update.')
#     if last_update_data['payevery_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
#         print('payevery has not been started for a long time: starting...')
#         start_payevery(db)
#     else:
#         if log:
#             print('payevery was started recently. All is ok.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess payevery.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start payevery).')
        print('--check: check payevery last update.')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --payevery-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('PAY EVERY')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_payevery(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_payevery(last_update_data, db, True)

    print('payevery subprocess stopped successfully.')
