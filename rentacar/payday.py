'''
PAY DAY
When it`s time to pay for charging of rental, this program send sms to renter about he need to pay for charging of rental and create payday task.
Also, if renter exceeded limit of mil, this program add penalty to renter - (current odometer - odometer before last payday - limit) * 0.15$
(migrated from paylimit module). When starts, add payday task, add pay_contract for renta price summ, update payday_odom, add history about
payday_odom updating, and, if it need, create pay_contract for extra mil summ.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all contracts, payday_last_update will update to current time.

Collection: Contract
Group: rentacar
Launch time: 11:57 [rentacar]
Marks: last-update, sms, limit-28-upd
'''

from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size


from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, to_mime_format, get_last_day
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db, get_car
from rentacar.str_config import PAYLIMIT_NAME_PAY, PAYLIMIT_SUM_COEFFICIENT, USER, PAYDAY_HISTORY_CHANGE, PAYDAY_HISTORY_EDIT

logdata = Log('payday.py')
print = logdata.print

def start_payday(db: client):
    """check if the day is overdue

    Args:
        db (client): database
    """
    print('start payday.')
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())

    # filtering contracts
    for contract in contracts.copy():
        payday = min(contract['pay_day'].astimezone(texas_tz).day, get_last_day())
        if has_key(contract, 'last_payday'):
            if to_mime_format(contract['last_payday']) == to_mime_format(dt.now(texas_tz)) or contract['pay_day'].astimezone(texas_tz).day > dt.now(texas_tz).day:
                contracts.remove(contract)
                continue
        if payday != dt.now(texas_tz).day or not contract['Active'] or to_mime_format(contract['begin_time']) == to_mime_format(dt.now(texas_tz)):
            contracts.remove(contract)

    for contract in contracts:
        print(f'write payday {contract["ContractName"]}')
        car: dict = get_car(db, contract['nickname'])
        # MIGRATED TO payevery module
        # create_payday(db, contract, car['odometer'])

        begin_odometer: int = 0
        if has_key(contract, 'Payday_odom'):
            begin_odometer = contract['Payday_odom']
        else:
            begin_odometer = contract['Begin_odom']

        if car['odometer'] - begin_odometer > contract['limit'] and contract['limit'] != 0:
            create_paylimit(db, car['odometer'], begin_odometer, contract['limit'], contract)

        if '--read-only' not in argv:
            db.collection('Contract').document(contract['_firebase_document_id']).update({
                'Payday_odom': car['odometer'],
                'last_payday': dt.now(texas_tz)
            })
            create_history(db, begin_odometer, car['odometer'], contract)
        else:
            print('history not created and payday_odom not updated because of "--read-only" flag.')

    print(f'total payday contracts: {len(contracts)}')

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'payday_update': dt.now(texas_tz)})
    else:
        print('payday last update not updated because of "--read-only" flag.')
    print('set last payday update.')

# MIGRATED TO payevery module
# def create_payday(db: client, contract: dict, odometer: int):
#     """Create a payment task and add it to the database

#     Args:
#         db (client): database
#         contract (dict): contract data
#         odometer (int): current odometer
#     """
#     print(f'write payday - nickname: {contract["nickname"]}')
#     if '--read-only' not in argv:
#         db.collection('Task').add({
#             'id': randint(10000, 20000),
#             'comment': PAYDAY_TASK_COMMENT.replace('{payday}', contract["pay_day"].day),
#             'name_task': PAYDAY_NAME_TASK,
#             'nickname': contract['nickname'],
#             'date': dt.now(texas_tz),
#             'photo_task': [PAYDAY_IMAGE],
#             'status': True,
#             'post': False,
#             'user': USER,
#             'ContractName': contract['ContractName']
#         })
#         db.collection('Pay_contract').add({
#             'nickname': contract['nickname'],
#             'ContractName': contract['ContractName'],
#             'date': dt.now(texas_tz),
#             'sum': contract['renta_price'],
#             'name_pay': PAYDAY_NAME_PAY,
#             'expense': True,
#             'odometer': odometer,
#             'user': USER,
#             'owner': True
#         })
#     else:
#         print('payday task and pay not created because of "--read-only" flag.')

#     if has_key(contract, 'renternumber') and '--read-only' not in argv:
#         send_sms(contract['renternumber'][0], PAYDAY_TEXT)
#         if has_key(contract, 'renter'):
#             add_inbox(db, contract['renternumber'][0], PAYDAY_TEXT, contract['ContractName'], contract['renter'])
#         else:
#             add_inbox(db, contract['renternumber'][0], PAYDAY_TEXT, contract['ContractName'], None)
#     else:
#         if '--read-only' in argv:
#             print('sms not sent because of "--read-only" flag.')

def create_paylimit(db: client, current_odometer: int, begin_odometer: int, limit: int, contract: dict):
    """Create a new paylimit for the given amount of odometer

    Args:
        db (client): database
        current_odometer (int): car odometer 
        begin_odometer (int): begin odom or payday odom
        limit (int): limit mil
        contract (dict): contract data
    """
    if '--read-only' not in argv:
        print(f'write paylimit {contract["nickname"]}, old odometer: {begin_odometer}, new odometer: {current_odometer}, limit: {limit}, extra \
mil: {current_odometer - begin_odometer - limit}.')
        db.collection('Pay_contract').add({
            'ContractName': contract['ContractName'],
            'date': dt.now(texas_tz),
            'expense': True,
            'name_pay': PAYLIMIT_NAME_PAY.replace('{limit}', str(current_odometer - begin_odometer - limit)),
            'nickname': contract['nickname'],
            'odometer': current_odometer,
            'sum': float(round((current_odometer - begin_odometer - limit) * PAYLIMIT_SUM_COEFFICIENT)),
            'user': USER,
            'owner': True,
            'category': 'extra'
        })
    else:
        print('paylimit pay not created because of "--read-only" flag.')

def create_history(db: client, begin_odometer: int, current_odometer: int, contract: dict):
    """Create a payment history record for each time in the database

    Args:
        db (client): [description]
        begin_odometer (int): [description]
        current_odometer (int): [description]
        contract (dict): [description]
    """
    extra_mil = current_odometer - begin_odometer - contract['limit']
    db.collection('History').add({
        'change': PAYDAY_HISTORY_CHANGE,
        'edit': PAYDAY_HISTORY_EDIT.replace('{old_odometer}', str(begin_odometer)).replace('{new_odometer}', str(current_odometer)).replace('{extra}', \
f', extra: {extra_mil}' if extra_mil > 0 else ''),
        'date': dt.now(texas_tz),
        'nickname': contract['nickname'],
        'ContractName': contract['ContractName'],
        'user': USER
    })

def check_payday(last_update_data: dict, db: client, log: bool = False):
    """check the day of the last update

    Args:
        last_update_data (dict): last update
        db (client): database
        log (bool, optional): show logs. Defaults to False.
    """
    if log:
        print('check payday last update.')
    if last_update_data['payday_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('payday has not been started for a long time: starting...')
        start_payday(db)
    else:
        if log:
            print('payday was started recently. All is ok.')
