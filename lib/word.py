from sys import path, argv
from os.path import dirname, abspath, join
from os import get_terminal_size
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from docxtpl import DocxTemplate
from lib.log import Log
from lib.mods.timemod import dt, timedelta
from lib.str_config import SETTINGAPP_DOCUMENT_ID
from lib.mods.firemod import document, init_db, has_key, get_car, get_contract, client

logdata = Log('word.py')
print = logdata.print

folder = join(dirname(dirname(abspath(__file__))), 'exword_results')

def build(db: client, contractName: str):
    contract: dict = get_contract(db, contractName, 'ContractName')
    car: dict = get_car(db, contract['nickname'])
        
    if has_key(contract, 'renternumber'):
        if contract['renternumber'][0] != '-':
            phone = contract['renternumber'][0]
        else:
            phone = ''
    else:
        phone = '' 
        
    if has_key(car, 'plate'):
        if car['plate'] != '-':
            plate = car['plate']
        else:
            plate = ''
    else:
        plate = ''
        
    if has_key('limit'):
        if contract['limit'] > 0:
            limit = contract['limit']
        else:
            limit = '        '
    else:
        limit = '        '
        
    nickname = ''
    for i in car['nickname']:
        if i in list('0123456789'):
            nickname += i
        
    if has_key(contract, 'address'):
        address = contract['address']
    else:
        address = ''
        
    if has_key(contract, 'license'):
        license = contract['license']
    else:
        license = '             '
        
    if has_key(contract, 'licenseDate'):
        license_end = contract['licenseDate'].strftime('%m/%d/%Y')
    else:
        license_end = '        '
        
    if has_key(contract, 'state'):
        state = contract['state']
    else:
        state = '        '
    if has_key(car, 'color'):
        color = car['color']
    else:
        color = ''
        
    docx = DocxTemplate(join(folder, 'sample.docx'))
    context = {
        'nickname': nickname,
        'begin_time': contract['begin_time'].strftime('%m/%d/%Y'),
        'renter': contract['renter'],
        'make': car['make'],
        'model': car['model'],
        'color': color,
        'year': car['year_string'],
        'odometer': contract['Begin_odom'],
        'plate': plate,
        'vin': car['vin'],
        'insurance': contract['insurance'],
        'insurance_number': contract['insurance_number'],
        'sum': str(contract['renta_price']),
        'payday': contract['pay_day'].strftime('%-d'),
        'deposit': str(contract['zalog']),
        'limit': limit,
        'phone': phone,
        'address': address,
        'driving_license': license,
        'license_expiration': license_end,
        'state': state
    }
    docx.render(context)
    docx.save(join(folder, 'data.docx'))
        
def word_listener(db: client, bucket):
    print('initialize word listener.')
        
    def snapshot(document: list[document], changes, read_time):
        try:
            doc = document[0].to_dict()
            if doc['word_active'] == True:
                print(f'write docx {doc["word_contract"]}')
                build(doc['word_contract'], db)
                blob = bucket.blob(f'word/{doc["word_contract"]}-{dt.now().strftime("%d-%m-%H-%M-%S")}.docx')
                blob.upload_from_filename(join(folder, 'data.docx'))
                blob.make_public()
                print(f'write url to firestore: {blob.public_url}')
                db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({'word_active': False, 'word_url': blob.public_url})
            
        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from word snapshot]')
            quit(1)
    
    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)

if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess word.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')
        
    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--listener: activate word listener')
        print('')
        print('default flags:')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subprocess from watcher.py (use --word-only -t)')
    else:
        db: client = init_db()
        if '--listener' in argv:
            word_listener(db, bucket())
            while True:
                sleep(52)
            
    print('word subprocess stopped successfully.')