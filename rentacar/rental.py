'''
RENTAL AGREEMENT
The same as lease (earlier word), but there is slightly modified template/sample.
Activate:
 1. Choose contract (rentee_contract) in setting_app.
 2. Change rentee_active to True.
 3. Wait, and after few seconds link of rental file will appear in rentee_url.


Collection: setting-app
Old name: rentee
Group: exword
Launch time: - [exword] (snapshots only)
Marks: listener
'''

from sys import path, argv
from os.path import dirname, abspath, join
from os import get_terminal_size, _exit
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from traceback import format_exception
from docxtpl import DocxTemplate, RichText
from rentacar.log import Log
from rentacar.mods.timemod import dt, sleep, time
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.mods.firemod import document, init_db, has_key, get_car, get_contract, client, bucket
from requests import get
from config import TELEGRAM_LINK

logdata = Log('rental.py')
print = logdata.print

result_folder = join(dirname(dirname(abspath(__file__))), 'exword_results')
sample_folder = join(dirname(dirname(abspath(__file__))), 'exword_samples')

def check_value(data: dict, key: str, check: str = '-', default: str = ''):
    """Check if a value has a given key in a dictionary

    Args:
        data (dict): dictionary
        key (str): key
        check (str, optional): check key on this value. Defaults to '-'.
        default (str, optional): if key fail check, this value return. Defaults to ''.

    Returns:
        str: key or default value
    """
    if has_key(data, key):
        if data[key] != check:
            return data[key]
    return default

def build(db: client, contractName: str):
    """Build a sample file

    Args:
        db (client): database
        contractName (str): contract name
    """
    start_time = time()
    contract: dict = get_contract(db, contractName, 'ContractName', check_active=False)
    car: dict = get_car(db, contract['nickname'])

    if has_key(contract, 'renternumber'):
        if contract['renternumber'][0] != '-':
            phone = contract['renternumber'][0]
        else:
            phone = ''
    else:
        phone = ''

    plate = check_value(car, 'plate')

    if has_key(contract, 'limit'):
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

    if has_key(contract, 'licenseDate'):
        license_end = contract['licenseDate'].strftime('%m/%d/%Y')
    else:
        license_end = '        '

    if has_key(contract, 'discount_month'):
        if contract['discount_month'] > 0:
            discount = RichText()
            discount.add('5.1 EXCLUSIVE AGREEMENT AND MINIMUM RENTAL TERM. ', bold=True)
            discount.add(f'Agreement is deemed exclusive due to the discounted rental payment of ${round(contract["renta_price"] / 30, 1)} per \
day provided to the Rentee. As a condition of this exclusivity and discount, the Rentee agrees to a minimum rental term of \
{contract["discount_month"]} months from the effective date of this Agreement. If the Rentee terminates this Agreement prior to the completion \
of this {contract["discount_month"]} month minimum term, the Rentee shall be subject to an early termination penalty of $100, payable to the \
Rentor immediately upon termination, in addition to any other obligations or fees outlined in this Agreement.')
    else:
        discount = ''

    docx = DocxTemplate(join(sample_folder, 'rental.docx'))
    context = {
        'nickname': nickname,
        'begin_time': contract['begin_time'].strftime('%m/%d/%Y'),
        'renter': contract['renter'],
        'make': car['make'],
        'model': car['model'],
        'color': check_value(car, 'color'),
        'year': car['year_string'],
        'odometer': contract['Begin_odom'],
        'plate': plate,
        'vin': car['vin'],
        'insurance': contract['insurance'],
        'insurance_number': contract['insurance_number'],
        'sum': str(contract['renta_price']),
        'payday': contract['pay_day'].strftime('%#d'),
        'deposit': str(contract['zalog']),
        'limit': limit,
        'phone': phone,
        'address': check_value(contract, 'address'),
        'driving_license': check_value(contract, 'license', default='             '),
        'license_expiration': license_end,
        'state': check_value(contract, 'state', default='        '),
        'discount': discount
    }
    docx.render(context)
    docx.save(join(result_folder, 'rental.docx'))
    print(f'Rental build completed. Built contract: {contractName}. Time: {round(time() - start_time, 2)} seconds.')

def rental_listener(db: client, bucket):
    """start rental listener

    Args:
        db (client): database
        bucket (bucket): firestore bucket
    """
    print('initialize rental listener.')

    def snapshot(document: list[document], changes, read_time):
        """snapshot the rental contract

        Args:
            document (list[document]): document
            changes ([type]): nothing
            read_time ([type]): nothing
        """
        try:
            doc = document[0].to_dict()
            if doc['rentee_active']:
                print(f'write docx {doc["rentee_contract"]} (rental)')
                build(db, doc['rentee_contract'])
                if '--read-only' not in argv:
                    blob = bucket.blob(f'word/{doc["rentee_contract"]}-{dt.now().strftime("%d-%m-%H-%M-%S")}.docx')
                    blob.upload_from_filename(join(result_folder, 'rental.docx'))
                    blob.make_public()
                    print(f'write url to firestore: {blob.public_url}')
                else:
                    print('file not upload because of "--read-only" flag.')
                if '--read-only' not in argv:
                    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({
                        'rentee_active': False,
                        'rentee_url': blob.public_url
                    })
                else:
                    print('rentee_active not reseted because of "--read-only" flag.')

        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from rental snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)

if __name__ == '__main__':
    logdata.logfile('\n')
    run = ''
    for i in argv:
        run += i + ' '
    logdata.log_init(run)

    print('start subprocess rental.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--listener: activate rental listener')
        print('')
        print('default flags:')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this\
subprocess from watcher.py (use --rental-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('RENTAL AGREEMENT')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--listener' in argv:
            rental_listener(db, bucket())
            while True:
                sleep(52)

    print('rental subprocess stopped successfully.')
