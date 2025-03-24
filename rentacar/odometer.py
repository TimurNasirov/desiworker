'''
ODOMETER
Update all odometers of cars from bouncie. Starts at launch time and when actual_dometer is True in firebase.
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all cars, odometer_last_update will update to current time.

Collection: cars
Group: rentacar
Launch time: 11:50, 23:51, 6:00 [odometer]
Marks: last-update, listener
'''

from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size, _exit
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from traceback import format_exception
from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, sleep, time
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db, document
from rentacar.str_config import TEMPAPP_DOCUMENT_ID, SETTINGAPP_DOCUMENT_ID
from rentacar.mods.bouncie import get_apikey, get_odometer
from requests import get
from config import TELEGRAM_LINK

logdata = Log('odometer.py')
print = logdata.print

def start_odometer(db: client):
    """Update odometer

    Args:
        db (client): database
    """
    start_time = time()
    print('start odometer.')
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    auth_code: str = db.collection('Temp_APP').document(TEMPAPP_DOCUMENT_ID).get().to_dict()['AUTHBouncie']
    api_key: str = get_apikey(auth_code)

    for car in cars:
        update_odometer(db, api_key, car)

    if '--read-only' not in argv:
        print('set last odometer update.')
        db.collection('Last_update_python').document('last_update').update({'odometer_update': dt.now(texas_tz)})
    else:
        print('odometer last update not updated because of "--read-only" flag.')
    print(f'Odometer work completed. Updated cars: {len(cars)}. Time: {round(time() - start_time, 2)} seconds.')

def update_odometer(db: client, api_key: str, car: dict):
    """Update the odometer for a given car

    Args:
        db (client): database
        api_key (str): api key
        car (dict): car data
    """
    if has_key(car, 'device_imei'):
        odometer = get_odometer(api_key, car['device_imei'])

        if odometer != 'keep' and round(odometer) != round(car['odometer']):
            odometer = round(odometer)
            print(f'write odometer - nickname: {car["nickname"]}, vin: {car["vin"]}, odometer: {odometer}')

            if '--read-only' not in argv:
                db.collection('cars').document(car['_firebase_document_id']).update({'odometer': odometer})
            else:
                print('odometer not updated because of "--read-only" flag.')
        else:
            print(f'skip car - nickname: {car["nickname"]}')

def check_odometer(last_update_data: dict, db: client, log: bool = False):
    """Check the odometer last update time

    Args:
        last_update_data (dict): last update
        db (client): database
        log (bool, optional): show logs. Defaults to False.
    """
    if log:
        print('check odometer last update.')
    if last_update_data['odometer_update'].astimezone(texas_tz) + timedelta(hours=8) <= dt.now(texas_tz):
        print('odometer has not been started for a long time: starting...')
        start_odometer(db)
    else:
        if log:
            print('odometer was started recently. All is ok.')

def odometer_listener(db: client):
    """start odometer listener

    Args:
        db (client): database
    """
    print('initialize odometer listener.')
    def snapshot(document: list[document], changes, read_time: dt):
        try:
            setting = document[0].to_dict()
            if setting['actual_odometer']:
                print('update odometer because of snapshot listener detect actual_odometer is True.')
                start_odometer(db)
        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from odometer snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)


if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess odometer.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--test: test (start odometer).')
        print('--check: check odometer last update.')
        print('--listener: activate odometer listener')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --odometer-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('ODOMETER')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--test' in argv:
            start_odometer(db)
        elif '--check' in argv:
            last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
            check_odometer(last_update_data, db, True)
        elif '--listener' in argv:
            odometer_listener(db)
            while True:
                sleep(52)

    print('odometer subprocess stopped successfully.')
