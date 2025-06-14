from mods.firemod import init_db, client, to_dict_all
from mods.timemod import texas_tz, dtime

db: client = init_db()
pays = to_dict_all(db.collection('Pay_contract').get())
for pay in pays:
    if pay['name_pay'] == 'First Pay' and dtime(19,0) <= pay['date'].astimezone(texas_tz).time() <= dtime(23,59,59):
        print(pay)