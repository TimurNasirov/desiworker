"""
SALDO
Every day calculates contracts incomes and expenses, and add this summ in last_saldo to renter can know hpw much money renter need to pay.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all cars, saldo_last_update will update to current time.

Collection: Contract
Group: rentacar
Launch time: 11:57 [rentacar]
Marks: last-update
"""
from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size, _exit
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from traceback import format_exception
from rentacar.mods.firemod import has_key, to_dict_all, client, get_car, get_contract, document, init_db
from rentacar.mods.timemod import dt, texas_tz, time
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.log import Log
from requests import get
from config import TELEGRAM_LINK

logdata = Log('saldo.py')
print = logdata.print

def start_saldo(db: client):
    start_time = time()
    print('start saldo.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())

    pays: list[dict] = to_dict_all(db.collection('Pay_contract').get())
    tolls: list[dict] = to_dict_all(db.collection('Toll').get())
    for contract in contracts:
        income = 0
        expense = 0
        toll_sum = 0
        for pay in pays:
            if pay['ContractName'] == contract['ContractName']:
                if has_key(pay, 'delete'):
                    if pay['delete']:
                        continue
                if has_key(pay, 'income'):
                    if pay['income']:
                        income += pay['sum']
                if has_key(pay, 'expense'):
                    if pay['expense']:
                        expense += pay['sum']

        car = get_car(db, contract['nickname'])
        if has_key(car, 'plate'):
            if car['plate'] != '' and car['plate'] != '-':
                for toll in tolls:
                    if has_key(toll, 'plate') and not toll['paid']:
                        if toll['plate'] == car['plate']:
                            toll_sum += toll['transaction']

        summ = round(income - expense - toll_sum, 2)
        print(f'write saldo - ContractName: {contract["ContractName"]}, sum: {summ}.')
        if '--read-only' not in argv:
            db.collection('Contract').document(contract['_firebase_document_id']).update({'last_saldo': summ})
        else:
            print('saldo not writed because of "--read-only" flag.')

    print('set last saldo update.')
    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'saldo_update': dt.now(texas_tz)})
        db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({'actual_saldo': False})
    else:
        print('saldo last update not updated because of "--read-only" flag.')
    print(f'Saldo work completed. Updated contracts: {len(contracts)}. Time: {round(time() - start_time, 2)} seconds.')

def start_onecar_saldo(db: client, contract_name: str):
    start_time = time()
    contract: dict = get_contract(db, contract_name, by='ContractName', check_active=False)
    car: dict = get_car(db, contract['nickname'])

    pays: list[dict] = to_dict_all(db.collection('Pay_contract').get())
    tolls: list[dict] = to_dict_all(db.collection('Toll').get())

    income = 0
    expense = 0
    toll_sum = 0
    for pay in pays:
        if pay['ContractName'] == contract['ContractName']:
            if has_key(pay, 'delete'):
                if pay['delete']:
                    continue
            if has_key(pay, 'income'):
                if pay['income']:
                    income += pay['sum']
            if has_key(pay, 'expense'):
                if pay['expense']:
                    expense += pay['sum']

    if has_key(car, 'plate'):
        if car['plate'] != '' and car['plate'] != '-':
            for toll in tolls:
                if has_key(toll, 'plate') and not toll['paid']:
                    if toll['plate'] == car['plate']:
                        toll_sum += toll['transaction']

    summ = round(income - expense - toll_sum, 2)
    print(f'write saldo {contract["nickname"]}, sum: {summ}.')
    if '--read-only' not in argv:
        db.collection('Contract').document(contract['_firebase_document_id']).update({'last_saldo': summ})
    else:
        print('saldo not writed because of "--read-only" flag.')

    print('set actual saldo to False.')
    if '--read-only' not in argv:
        db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({'actual_saldo': False})
    else:
        print('actual saldo not setted because of "--read-only" flag.')
    print(f'Saldo work completed. Updated contract: {contract_name}. Time: {round(time() - start_time, 2)} seconds.')

def check_saldo(last_update_data: dict, db: client, log: bool = False):
    if log:
        print('check saldo last update.')
    if last_update_data['saldo_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('saldo has not been started for a long time: starting...')
        start_saldo(db)
    else:
        if log:
            print('saldo was started recently. All is ok.')

def saldo_listener(db: client):
    print('initialize saldo listener.')
    def snapshot(document: list[document], changes, read_time: dt):
        try:
            setting = document[0].to_dict()
            if setting['actual_saldo']:
                if setting['saldo_contract'] == 'all':
                    print('update all saldo because of snapshot listener detect actual_saldo is True.')
                    start_saldo(db)
                else:
                    print(f'update {setting["saldo_contract"]} contract saldo because of snapshot listener detect actual_saldo is True.')
                    start_onecar_saldo(db, setting['saldo_contract'])

        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from saldo snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)


if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess saldo.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start saldo).')
        print('--check: check saldo last update.')
        print('--listener: activate saldo listener')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --saldo-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('saldo')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_saldo(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_saldo(last_update_data, db, True)
        elif '--listener' in argv:
            saldo_listener(db)
            while True:
                sleep(52)

    print('saldo subprocess stopped successfully.')