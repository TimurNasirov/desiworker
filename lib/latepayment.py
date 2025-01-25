from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
from random import randint
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from lib.log import Log
from lib.mods.timemod import dt, timedelta, texas_tz, now_with_payday, to_MY_format
from lib.mods.firemod import to_dict_all, has_key, client, init_db, get_contract, get_car
from lib.mods.sms import send_sms, add_inbox, LATEPAYMENT_TEXT
from lib.str_config import LATEPAYMENT_NAME_PAY, USER

logdata = Log('latepayment.py')
print = logdata.print

def start_latepayment(db: client):
    print('start latepayment.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    pays: list[dict] = to_dict_all(db.collection('Pay_contract').get())
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    
    for pay in pays.copy():
        if to_MY_format(pay['date']) != to_MY_format(dt.now(texas_tz)):
            pays.remove(pay)
        elif not has_key(pay, 'ContractName'):
            pays.remove(pay)
    
    for contract in contracts.copy():
        # "for" loop in 1 line: https://python-scripts.com/for-in-one-line
        # check if contract where its nickname in pays thats name_pay is "Late payment"
        if contract['ContractName'] in [pay['ContractName'] for pay in pays if pay['name_pay'] == 'Late payment' and pay['nickname'] == contract['nickname']]:
            contracts.remove(contract)
        else:
            if not contract['Active']:
                contracts.remove(contract)
    
    latepayment_count = 0
    prelatepayment_count = 0
    for contract in contracts.copy():
        car = [car for car in cars if car['nickname'] == contract['nickname']]
        if car == []: car = {'odometer': -1}
        else: car = car[0]
        if contract['ContractName'] == 'Contract-49M-TEST-1':
            print(now_with_payday(contract['pay_day']) + timedelta(days=3))
            print(dt.now(texas_tz))
        
        now = dt.now()
        if dt(year=now.year, month=now.month, day=contract['pay_day'].day) + timedelta(days=5) == dt(year=now.year, month=now.month, day=now.day) and to_MY_format(contract['begin_time']) != to_MY_format(dt.now(texas_tz)) and contract['last_saldo'] < -contract['renta_price']:
            latepayment_count += 1
            create_pay(db, contract, car)
        
        elif dt(year=now.year, month=now.month, day=contract['pay_day'].day) + timedelta(days=3) == dt(year=now.year, month=now.month, day=now.day) and to_MY_format(contract['begin_time']) != to_MY_format(dt.now(texas_tz)) and contract['last_saldo'] < -contract['renta_price'] and has_key(contract, 'renternumber'):
            prelatepayment_count += 1
            print(f'send pre-latepayment sms, nickname: {contract["nickname"]}')
            if not '--read-only' in argv:
                send_sms(contract['renternumber'][0], LATEPAYMENT_TEXT.replace('{debt}', contract['last_saldo'])),
                if has_key(contract, 'renter'):
                    add_inbox(db, contract['renternumber'][0], contract['ContractName'], contract['renter'], LATEPAYMENT_TEXT.replace('{debt}', contract['last_saldo']))
                else:
                    add_inbox(db, contract['renternumber'][0], LATEPAYMENT_TEXT.replace('{debt}', contract['last_saldo']), contract['ContractName'], contract['renter'])
            else:
                print('sms not sent because of "--read-only" flag.')
    
    print(f'Total latepayment contracts: {latepayment_count}')
    print(f'Total pre-latepayment contracts: {prelatepayment_count}')
    
    if '--read-only' not in argv:
        db.collection('Last_update_python').doc('last_update').update({'latepayment_update': dt.now(texas_tz)})
    else:
        print('latepayment last update not updated because of "--read-only" flag.')
    print('set last latepayment update.')

def create_pay(db: client, contract: dict, car: dict):
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
            'odometer': car['odometer']
        })
    else:
        print('pay not created because of "--read-only" flag.')

def check_latepayment(last_update_data: dict, db: client, log: bool = False):
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
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subprocess from watcher.py (use --latepayment-only -t)')
    else:
        db: client = init_db()
        if '--test' in argv:
            start_latepayment(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_latepayment(last_update_data, db, True)
            
    print('latepayment subprocess stopped successfully.')