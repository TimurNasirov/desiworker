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
from os import _exit


from traceback import format_exception
from rentacar.mods.firemod import has_key, to_dict_all, client, get_car, get_contract, document, FieldFilter
from rentacar.mods.timemod import dt, texas_tz, time, timedelta
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.log import Log
from requests import get
from rentacar.config import TELEGRAM_LINK

logdata = Log('saldo.py')
print = logdata.print

def start_saldo(db) -> None:
    start_time = time()
    reads = 0
    print('start saldo.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    reads += len(contracts)

    for contract in contracts:
        income = 0
        expense = 0
        toll_sum = 0
        pays = to_dict_all(db.collection('Pay_contract')
            .where(filter=FieldFilter('ContractName', '==', contract['ContractName'])).get())
        reads += len(pays)
        for pay in pays:
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
                tolls = to_dict_all(db.collection('Toll')
                    .where(filter=FieldFilter('plate', '==', car['plate']))
                    .where(filter=FieldFilter('paid', '==', False)).get())
                reads += len(tolls)
                toll_sum = sum([toll['transaction'] for toll in tolls])

        summ = round(income - expense - toll_sum, 2)
        # print(f'write saldo - ContractName: {contract["ContractName"]}, sum: {summ}.')
        if '--read-only' not in argv:
            contract['_firebase_reference'].update({'last_saldo': summ})
        else:
            print('saldo not wrote because of "--read-only" flag.')

    print('set last saldo update.')
    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'saldo_update': dt.now(texas_tz)})
        db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({'actual_saldo': False})
    else:
        print('saldo last update not updated because of "--read-only" flag.')
    print(
        f'saldo work completed. Updated contracts: {len(contracts)}.'
        f' Time: {round(time() - start_time, 2)} seconds. Reads: {reads}'
    )

def start_onecar_saldo(db, contract_name: str) -> None:
    start_time = time()
    contract: dict = get_contract(db, contract_name, 'ContractName', False)
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
    print(f'write saldo {contract["ContractName"]}, sum: {summ}.')
    if '--read-only' not in argv:
        db.collection('Contract').document(contract['_firebase_document_id']).update({'last_saldo': summ})
    else:
        print('saldo not writed because of "--read-only" flag.')

    if '--read-only' not in argv:
        db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({'actual_saldo': False})
    else:
        print('actual saldo not setted because of "--read-only" flag.')
    # print(f'Saldo work completed. Updated contract: {contract_name}. Time: {round(time() - start_time, 2)} seconds.')

def check_saldo(last_update_data: dict, db, log: bool = False) -> None:
    if log:
        print('check saldo last update.')
    if last_update_data['saldo_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('saldo has not been started for a long time: starting...')
        start_saldo(db)
    else:
        if log:
            print('saldo was started recently. All is ok.')

def saldo_listener(db) -> None:
    print('initialize saldo listener.')
    def snapshot(document: list[document], _, __) -> None:
        try:
            setting = document[0].to_dict()
            if not setting:
                raise ValueError('setting is null')
            if setting['actual_saldo']:
                if setting['saldo_contract'] == 'all':
                    print('update all saldo because of snapshot listener detect actual_saldo is True.')
                    start_saldo(db)
                else:
                    start_onecar_saldo(db, setting['saldo_contract'])

        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from saldo snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)
