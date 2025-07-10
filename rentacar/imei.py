'''
IMEI
Compare imei in bouncie and in firebase. If there is difference, create task.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all cars, imei_last_update will update to current time.

Collection: cars
Group: rentacar
Launch time: 12:00 [imei]
Marks: bouncie
'''

from sys import argv
from typing import Literal

from rentacar.log import Log
from rentacar.mods.timemod import dt, texas_tz, time
from rentacar.mods.firemod import to_dict_all, has_key, client
from rentacar.str_config import TEMPAPP_DOCUMENT_ID
from rentacar.mods.bouncie import get_apikey, get_imei

logdata = Log('imei.py')
print = logdata.print

def start_imei(db: client) -> None:
    """Update imei

    Args:
        db (client): database
    """
    start_time = time()
    print('start imei.')

    cars: list[dict] = to_dict_all(db.collection('cars').get())
    auth_code: str = db.collection('Temp_APP').document(TEMPAPP_DOCUMENT_ID).get().to_dict()['AUTHBouncie']
    bcars = get_imei(get_apikey(auth_code))

    tasks_count = 0
    lost_count = 0
    for car in cars:
        for bcar in bcars:
            if car['vin'] == bcar['vin']:
                tasks_count += compare_imei(db, bcar, car)
                break
        else:
            print(f'cannot find car with nickname {car["nickname"]} in bouncie.')
            lost_count += 1

    print(f'imei work completed. Stats [BETA]:')
    print(f' - tasks created: {tasks_count}')
    print(f' - car checked: {len(cars)}')
    print(f' - lost cars: {lost_count}')
    print(f' - time: {round(time() - start_time, 2)} seconds.')

def compare_imei(db: client, bcar: dict, car: dict) -> Literal[False] | Literal[True]:
    """Update the imei for a given car

    Args:
        db (client): database
        api_key (str): api key
        car (dict): car data
    """
    if has_key(car, 'device_imei'):
        imei = bcar['imei']

        if imei != car['device_imei']:
            print(f'write imei - nickname: {car["nickname"]}, vin: {car["vin"]}, imei: {imei}.')

            if '--read-only' not in argv:
                db.collection('Task').add({
                    'date': dt.now(texas_tz),
                    'name_task': 'IMEI difference found',
                    'comment': f'firebase imei: {car["device_imei"]}/bouncie imei: {imei}',
                    'nickname': car['nickname']
                })
            else:
                print('imei task not created because of "--read-only" flag.')
            return True
        else:
            return False
    return False