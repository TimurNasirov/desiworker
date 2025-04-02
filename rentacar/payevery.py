from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
from random import randint
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, time
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db, get_car
from rentacar.mods.sms import send_sms, add_inbox, PAYDAY_TEXT, sms_block_check
from rentacar.str_config import PAYDAY_IMAGE, PAYDAY_NAME_PAY, PAYDAY_TASK_COMMENT, USER

logdata = Log('payevery.py')
print = logdata.print

def start_payevery(db: client):
    """Initiates the daily payment process for active contracts."""
    start_time = time()
    print('start payevery.')
    contracts = [c for c in to_dict_all(db.collection('Contract').get()) if c['Active']]
    pays = [p for p in to_dict_all(db.collection('Pay_contract').get()) if has_key(p, 'category') and has_key(p, 'ContractName')]
    now = dt.now(texas_tz).date()

    pays_count = 0
    for contract in contracts:
        daily_rent_pays = [p for p in pays if p['ContractName'] == contract['ContractName'] and p['category'] == 'daily rent']
        is_payday = contract['pay_day'].strftime('%d') == now.strftime('%d')

        if is_payday or daily_rent_pays:
            car = get_car(db, contract['nickname'])
            last_date = max([p['date'] for p in daily_rent_pays]).date() if daily_rent_pays else now - timedelta(days=1)
            days_missed = (now - last_date).days

            if days_missed >= 0:
                for day in range(days_missed + 1):  # Include today
                    pay_date = last_date + timedelta(days=day + 1)  # Normalize to date only
                    if pay_date <= now:  # Compare dates only
                        create_payevery(db, contract, car['odometer'], dt.now(texas_tz).replace(year=pay_date.year, month=pay_date.month, day=pay_date.day))
                        pays_count += 1

    print(f'payevery completed. Stats: pays created: {pays_count}, contracts checked: {len(contracts)}, time: {round(time() - start_time, 2)}')

def create_payevery(db: client, contract: dict, odometer: int, pay_date: dt):
    """Creates a "daily rent" payment for a specific date."""
    print(f'write payevery - ContractName: {contract["ContractName"]} for {pay_date.strftime("%Y-%m-%d")}')
    if '--read-only' not in argv:
        db.collection('Pay_contract').add({
            'nickname': contract['nickname'],
            'ContractName': contract['ContractName'],
            'date': pay_date,
            'sum': contract['renta_price'] / 30,
            'name_pay': PAYDAY_NAME_PAY,
            'expense': True,
            'odometer': odometer,
            'user': USER,
            'owner': True,
            'category': 'daily rent'
        })
    else:
        print('payevery pay not created due to "--read-only" flag.')

def start_payevery2(db: client):
    """Initiates the process of creating PayDay tasks and sending SMS for contracts with insufficient balance."""
    start_time = time()
    print('start payevery (2).')
    contracts = [c for c in to_dict_all(db.collection('Contract').get()) if c['Active'] and has_key(c, 'last_saldo')]
    tasks = to_dict_all(db.collection('Task').get())
    pays = [p for p in to_dict_all(db.collection('Pay_contract').get()) if has_key(p, 'category') and has_key(p, 'ContractName')]

    tasks_count = 0
    for contract in contracts:
        if contract['nickname'] not in [t['nickname'] for t in tasks if t['name_task'] == 'PayDay' and t['status']] and contract['last_saldo'] <=\
            -contract['renta_price'] / 30 and contract['ContractName'] in [p['ContractName'] for p in pays if p['category'] == 'daily rent'] and\
            contract['pay_day'].strftime('%d') == dt.now().strftime('%d'):
            create_payevery2(db, contract)
            tasks_count += 1

    print(f'payevery 2 completed. Stats: tasks & sms created: {tasks_count}, contracts checked: {len(contracts)}, time: {round(time() - start_time, 2)}')

def create_payevery2(db: client, contract: dict):
    """Creates a PayDay task and sends an SMS to the renter if conditions are met."""
    print(f'write payevery 2 - ContractName: {contract["ContractName"]}')
    if '--read-only' not in argv:
        db.collection('Task').add({
            'id': randint(10000, 20000),
            'comment': PAYDAY_TASK_COMMENT.replace('{payday}', str(contract["pay_day"].day)),
            'name_task': 'PayDay',
            'nickname': contract['nickname'],
            'date': dt.now(texas_tz),
            'photo_task': [PAYDAY_IMAGE],
            'status': True,
            'post': False,
            'user': USER,
            'ContractName': contract['ContractName']
        })
        if has_key(contract, 'renternumber') and sms_block_check(contract):
            send_sms(contract['renternumber'][0], PAYDAY_TEXT)
            add_inbox(db, contract['renternumber'][0], PAYDAY_TEXT, contract['ContractName'], contract.get('renter'))
    else:
        print('payevery task/sms not created due to "--read-only" flag.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ' '.join(argv)
    logdata.log_init(command)

    print('start subprocess payevery.')
    if len(argv) == 1:
        print('not enough arguments. add -h for help.')
    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('-> run watcher.py for main process')
        print('--test: test (start payevery).')
        print('--check: check payevery last update.')
        print('flags: -h (help), --no-sms (disable SMS), --read-only (read-only mode)')
        print('WARNING: errors not caught in subprocess, use watcher.py with --payevery-only -t to fix')
        print('Description:')
        for line in __doc__.split('\n')[1:]:
            if line.strip() and line != 'PAY EVERY': print(line)
    else:
        db = init_db()
        if '--test' in argv:
            start_payevery(db)

    print('payevery subprocess stopped successfully.')