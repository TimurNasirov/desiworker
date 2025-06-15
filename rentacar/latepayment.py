'''
LATE PAYMENT
If renter don`t pay the charging of rental, 3 days after payday this programm will send sms to renter about he need to pay the charging of
rental, and if he don`t pay this program will add penalty of 50$. And, when renter come to office, he need to pay for charging of rental and
this penalty.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all contracts, latepayment_last_update will update to current time.

Collection: Contract
Group: rentacar
Launch time: 11:57 [rentacar]
Marks: last-update, sms, limit-28-upd
'''

from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, to_mime_format, get_last_day
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db
from rentacar.mods.sms import send_sms, add_inbox, LATEPAYMENT_TEXT, sms_block_check
from rentacar.str_config import LATEPAYMENT_NAME_PAY, USER

logdata = Log('latepayment.py')
print = logdata.print

def start_latepayment(db: client):
    """Start late payment

    Args:
        db (client): date
    """
    print('start latepayment.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    pays: list[dict] = to_dict_all(db.collection('Pay_contract').get())
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    tasks: list[dict] = to_dict_all(db.collection('Task').get())

    for pay in pays.copy():
        if to_mime_format(pay['date'].astimezone(texas_tz)) != to_mime_format(dt.now(texas_tz)):
            pays.remove(pay)
        elif not has_key(pay, 'ContractName'):
            pays.remove(pay)

    for contract in contracts.copy():
        # "for" loop in 1 line: https://python-scripts.com/for-in-one-line
        # check if contract where its nickname in pays thats name_pay is "Late payment"
        if contract['ContractName'] in [pay['ContractName'] for pay in pays if pay['name_pay'] == 'Late payment']:
            contracts.remove(contract)
        else:
            if not contract['Active']:
                contracts.remove(contract)

    for task in tasks.copy():
        if not task['status'] or task['name_task'] != 'PayDay' or not has_key(task, 'ContractName'):
            tasks.remove(task)

    latepayment_count = 0
    prelatepayment_count = 0
    for contract in contracts.copy():
        car = [car for car in cars if car['nickname'] == contract['nickname']]
        if car == []:
            car = {'odometer': -1}
        else:
            car = car[0]

        now = dt.now()
        contract_tasks = [task['date'].astimezone(texas_tz) for task in tasks if task['ContractName'] == contract['ContractName']]
        if contract_tasks != []:
            target_date = now.replace(day=min(max(contract_tasks).day, get_last_day()))
            if now.day == (target_date + timedelta(days=5)).day and contract['last_saldo'] < -contract['renta_price'] / 30.5:
                latepayment_count += 1
                create_pay(db, contract, car)

            elif now.day >= (target_date + timedelta(days=3)).day and contract['last_saldo'] < -contract['renta_price'] / 30.5 and \
                    has_key(contract, 'renternumber'):

                prelatepayment_count += 1
                print(f'send pre-latepayment sms - nickname: {contract["nickname"]}')
                if '--read-only' not in argv:
                    if sms_block_check(contract):
                        if send_sms(contract['renternumber'][0], LATEPAYMENT_TEXT):
                            if has_key(contract, 'renter'):
                                add_inbox(db, contract['renternumber'][0], LATEPAYMENT_TEXT,
                                    contract['ContractName'], contract['renter'])
                            else:
                                add_inbox(db, contract['renternumber'][0], LATEPAYMENT_TEXT,
                                    contract['ContractName'], None)
                        else:
                            send_sms(contract['renternumber'][0], LATEPAYMENT_TEXT)
                            print('retry failed - skip')
                else:
                    print('sms not sent because of "--read-only" flag.')

    print(f'total latepayment contracts: {latepayment_count}')
    print(f'total pre-latepayment contracts: {prelatepayment_count}')

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'latepayment_update': dt.now(texas_tz)})
    else:
        print('latepayment last update not updated because of "--read-only" flag.')
    print('set last latepayment update.')

def create_pay(db: client, contract: dict, car: dict):
    """create latepayment pay

    Args:
        db (client): database
        contract (dict): contract data
        car (dict): car data
    """
    print(f'write latepayment - nickname: {contract["nickname"]}')
    if '--read-only' not in argv:
        db.collection('Pay_contract').add({
            'ContractName': contract['ContractName'],
            'name_pay': LATEPAYMENT_NAME_PAY,
            'expense': True,
            'date': dt.now(texas_tz),
            'nickname': contract['nickname'],
            'sum': 50,
            'user': USER,
            'odometer': car['odometer'],
            'category': 'extra'
        })
    else:
        print('pay not created because of "--read-only" flag.')

def check_latepayment(last_update_data: dict, db: client, log: bool = False):
    """check latepayment last update

    Args:
        last_update_data (dict): last update
        db (client): database
        log (bool, optional): show logs. Defaults to False.
    """
    if log:
        print('check latepayment last update.')
    if last_update_data['latepayment_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('latepayment has not been started for a long time: starting...')
        start_latepayment(db)
    else:
        if log:
            print('latepayment was started recently. All is ok.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess latepayment.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start latepayment).')
        print('--check: check latepayment last update.')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --latepayment-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('LATE PAYMENT')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_latepayment(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_latepayment(last_update_data, db, True)

    print('latepayment subprocess stopped successfully.')
