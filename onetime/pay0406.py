from mods.firemod import init_db, client, to_dict_all, has_key
from mods.timemod import texas_tz, dt, date
from time import time

db: client = init_db()
pays = to_dict_all(db.collection('Pay_contract').get())
count = 0
start = time()
for pay in pays:
    if has_key(pay, 'category'):
        if dt(2025, 6, 4, 0, 0, 15).replace(tzinfo=None) < pay['date'].astimezone(texas_tz).replace(tzinfo=None) <\
            dt(2025, 6, 4, 0, 2, 55).replace(tzinfo=None) and pay['category'] == 'daily rent':
            pay['_firebase_reference'].update({'sum': pay['sum'] * 30.5 / 30})
            print('update pay for contract', pay['ContractName'])
            count += 1
print(f'total updated: {count}, time: {time() - start}')