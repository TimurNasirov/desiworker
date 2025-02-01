from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
from random import randint
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from lib.log import Log
from lib.mods.timemod import dt, timedelta, texas_tz, to_MY_format
from lib.mods.firemod import to_dict_all, has_key, client, init_db, get_contract, get_car
from lib.mods.sms import send_sms, add_inbox, PAYDAY_TEXT
from lib.str_config import PAYDAY_IMAGE, PAYDAY_IMAGE, PAYDAY_NAME_PAY, PAYDAY_NAME_TASK, PAYDAY_TASK_COMMENT, PAYLIMIT_NAME_PAY, PAYLIMIT_SUM_COEFFICIENT, USER, PAYDAY_HISTORY_CHANGE, PAYDAY_HISTORY_EDIT

logdata = Log('payday.py')
print = logdata.print

def start_payday(db: client):
    print('start payday.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    
    # filtering contracts
    for contract in contracts.copy():
        if timedelta(days=contract['pay_day'].day) > timedelta(days=dt.now(texas_tz).day) or not contract['Active'] or to_MY_format(contract['begin_time']) == to_MY_format(dt.now(texas_tz)):
            contracts.remove(contract)
            
    tasks: list[dict] = to_dict_all(db.collection('Task').get())
    #remove tasks
    for task in tasks.copy():
        if to_MY_format(task['date']) != to_MY_format(dt.now(texas_tz)):
            tasks.remove(task)
            
    for contract in contracts.copy():
        # "for" loop in 1 line: https://python-scripts.com/for-in-one-line
        # check if contract where its nickname in tasks thats name_task is "payday"
        if contract['nickname'] in [task['nickname'] for task in tasks if task['name_task'] == 'PayDay']:
            contracts.remove(contract)
            
    for contract in contracts:
        car: dict = get_car(db, contract['nickname'])
        create_payday(db, contract, car['odometer'])
        
        begin_odometer: int = 0
        if has_key(contract, 'Payday_odom'):
            begin_odometer = contract['Payday_odom']
        else:
            begin_odometer = contract['Begin_odom']
        
        if car['odometer'] - begin_odometer > contract['limit'] and contract['limit'] != 0:
            create_paylimit(db, car['odometer'], begin_odometer, contract['limit'], contract)
        
        if '--read-only' not in argv:
            db.collection('Contract').document(contract['_firebase_document_id']).update({
                'Payday_odom': car['odometer']
            })
    
    print(f'total payday contracts: {len(contracts)}')
    
    if '--read-only' not in argv:
        db.collection('Last_update_python').doc('last_update').update({'payday_update': dt.now(texas_tz)})
    else:
        print('payday last update not updated because of "--read-only" flag.')
    print('set last payday update.')

def create_payday(db: client, contract: dict, odometer: int):
    print(f'write payday - nickname: {contract["nickname"]}')
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
        db.collection('Pay_contract').add({
            'nickname': contract['nickname'],
            'ContractName': contract['ContractName'],
            'date': dt.now(texas_tz),
            'sum': contract['renta_price'],
            'name_pay': PAYDAY_NAME_PAY,
            'expense': True,
            'odometer': odometer,
            'user': USER,
            'owner': True
        })
    else:
        print('payday task and pay not created because of "--read-only" flag.')
    
    if has_key(contract, 'renternumber') and not '--read-only' in argv:
        send_sms(contract['renternumber'][0], PAYDAY_TEXT),
        if has_key(contract, 'renter'):
            add_inbox(db, contract['renternumber'][0], PAYDAY_TEXT, contract['ContractName'], contract['renter'])
        else:
            add_inbox(db, contract['renternumber'][0], PAYDAY_TEXT, contract['ContractName'], None)
    else:
        if '--read-only' in argv:
            print('sms not sent because of "--read-only" flag.')

def create_paylimit(db: client, current_odometer: int, begin_odometer: int, limit: int, contract: dict):
    if '--read-only' not in argv:
        print(f'write paylimit {contract["nickname"]}, old odometer: {begin_odometer}, new odometer: {current_odometer}, limit: {limit}, extra mil: {current_odometer - begin_odometer - limit}.')
        db.collection('Pay_contract').add({
            'ContractName': contract['ContractName'],
            'date': dt.now(texas_tz),
            'expense': True,
            'name_pay': PAYLIMIT_NAME_PAY.replace('{limit}', current_odometer - begin_odometer - limit),
            'nickname': contract['nickname'],
            'odometer': current_odometer,
            'summ': float(round((current_odometer - begin_odometer - limit) * PAYLIMIT_SUM_COEFFICIENT)),
            'user': USER,
            'owner': True
        })
    else:
        print('paylimit pay not created because of "--read-only" flag.')

def create_history(db: client, begin_odometer: int, current_odometer: int, limit: int, contract: dict):
    extra_mil = current_odometer - begin_odometer - limit
    if '--read-only' not in argv:
        db.collection('History').add({
            'change': PAYDAY_HISTORY_CHANGE,
            'edit': PAYDAY_HISTORY_EDIT.replace('{old_odometer}', begin_odometer).replace('{new_odometer}', current_odometer).replace('{extra}', f', extra: {extra_mil}' if extra_mil > 0 else ''),
            'date': dt.now(texas_tz),
            'nickname': contract['nickname'],
            'ContractName': contract['ContractName'],
            'user': USER
        })
    else:
        print('history not created because of "--read-only" flag.')

def check_payday(last_update_data: dict, db: client, log: bool = False):
    if log:
        print('check payday last update.')
    if last_update_data['payday_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('payday has not been started for a long time: starting...')
        start_payday(db)
    else:
        if log:
            print('payday was started recently. All is ok.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess payday.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')
        
    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start payday).')
        print('--check: check payday last update.')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subprocess from watcher.py (use --payday-only -t)')
    else:
        db: client = init_db()
        if '--test' in argv:
            start_payday(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_payday(last_update_data, db, True)
            
    print('payday subprocess stopped successfully.')