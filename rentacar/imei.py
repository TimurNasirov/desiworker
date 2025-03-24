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

from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from rentacar.log import Log
from rentacar.mods.timemod import dt, texas_tz, time
from rentacar.mods.firemod import to_dict_all, has_key, client
from rentacar.str_config import TEMPAPP_DOCUMENT_ID
from rentacar.mods.bouncie import get_apikey, get_imei

logdata = Log('imei.py')
print = logdata.print

def start_imei(db: client):
    """Update imei

    Args:
        db (client): database
    """
    start_time = time()
    print('start imei.')
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    auth_code: str = db.collection('Temp_APP').document(TEMPAPP_DOCUMENT_ID).get().to_dict()['AUTHBouncie']
    api_key: str = get_apikey(auth_code)

    for car in cars:
        compare_imei(db, api_key, car)

    if '--read-only' not in argv:
        print('set last imei update.')
        db.collection('Last_update_python').document('last_update').update({'imei_update': dt.now(texas_tz)})
    else:
        print('imei last update not updated because of "--read-only" flag.')
    print(f'imei work completed. Updated cars: {len(cars)}. Time: {round(time() - start_time, 2)} seconds.')

def compare_imei(db: client, api_key: str, car: dict):
    """Update the imei for a given car

    Args:
        db (client): database
        api_key (str): api key
        car (dict): car data
    """
    if has_key(car, 'device_imei'):
        imei = get_imei(api_key, car['device_imei'])

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
                print('imtaskei not created because of "--read-only" flag.')
        else:
            print(f'no difference found - nickname: {car["nickname"]}, imei: {imei}.')

# def check_imei(last_update_data: dict, db: client, log: bool = False):
#     """Check the imei last update time

#     Args:
#         last_update_data (dict): last update
#         db (client): database
#         log (bool, optional): show logs. Defaults to False.
#     """
#     if log:
#         print('check imei last update.')
#     if last_update_data['imei_update'].astimezone(texas_tz) + timedelta(hours=8) <= dt.now(texas_tz):
#         print('imei has not been started for a long time: starting...')
#         start_imei(db)
#     else:
#         if log:
#             print('imei was started recently. All is ok.')

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess imei.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start imei).')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --imei-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('imei')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_imei(db)

    print('imei subprocess stopped successfully.')
