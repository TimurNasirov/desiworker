from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
from random import randint
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from lib.log import Log
from lib.mods.timemod import dt, timedelta, texas_tz, sleep
from lib.mods.firemod import to_dict_all, has_key, client, init_db, document
from lib.str_config import TEMPAPP_DOCUMENT_ID, SETTINGAPP_DOCUMENT_ID
from lib.mods.bouncie import get_apikey, get_odometer

logdata = Log('odometer.py')
print = logdata.print

def start_odometer(db: client):
    print('start odometer.')
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    auth_code: str = db.collection('Temp_APP').document(TEMPAPP_DOCUMENT_ID).get().to_dict()['AUTHBouncie']
    api_key: str = get_apikey(auth_code)
    
    for car in cars:
        update_odometer(db, api_key, car)
    
    print(f'total odometer cars: {len(cars)}')
    
    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'odometer_update': dt.now(texas_tz)})
    else:
        print('odometer last update not updated because of "--read-only" flag.')
    print('set last odometer update.')

def update_odometer(db: client, api_key: str, car: dict):
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
    if log:
        print('check odometer last update.')
    if last_update_data['odometer_update'].astimezone(texas_tz) + timedelta(hours=8) <= dt.now(texas_tz):
        print('odometer has not been started for a long time: starting...')
        start_odometer(db)
    else:
        if log:
            print('odometer was started recently. All is ok.')

def odometer_listener(db: client):
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
            quit(1)
            
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
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subprocess from watcher.py (use --odometer-only -t)')
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
        