'''
LEASE AGREEMENT
When new contract creates, owner need an agreement with renter. In DesiCars app, there is button, and after owner created contract he need to
click in this button, he can download agreement lease file and print it on printer.
Lease argeement file will appear in firebase storage and its link will be in setting_app.
Activate:
 1. Choose contract (word_contract) in setting_app.
 2. Change word_active to True.
 3. Wait, and after few seconds link of lease file will appear in word_url.


Collection: setting-app
Old name: word
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
from rentacar.mods.timemod import dt, sleep, time, texas_tz
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.mods.firemod import document, init_db, has_key, get_car, get_contract, client, bucket
from rentacar.mods.docusign import sign
from requests import get
from config import TELEGRAM_LINK

logdata = Log('lease.py')
print = logdata.print

result_folder = '/rentacar/exword_results/' if '-d' in argv else join(dirname(abspath(__file__)), 'exword_results')
sample_folder = '/rentacar/exword_samples/' if '-d' in argv else join(dirname(abspath(__file__)), 'exword_samples')

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

def build(db: client, contract_name: str, add_sign: bool):
    """Build a sample file

    Args:
        db (client): database
        contract_name (str): contract name
    """
    start_time = time()
    contract: dict = get_contract(db, contract_name, 'ContractName', check_active=False)
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
            discount.add('5.1. EXCLUSIVE AGREEMENT AND MINIMUM LEASE TERM. ', bold=True)
            discount.add(f'Agreement is deemed exclusive due to the discounted lease payment of ${round(contract["renta_price"] / 30.5, 1)} per day \
provided to the Lessee. As a condition of this exclusivity and discount, the Lessee agrees to a minimum lease term of {contract["discount_month"]} \
months from the effective date of this Agreement. If the Lessee terminates this Agreement prior to the completion of this \
{contract["discount_month"]} month minimum term, the Lessee shall be subject to an early termination penalty of $100, payable to the Lessor \
immediately upon termination, in addition to any other obligations or fees outlined in this Agreement.')
        else:
            discount = ''
    else:
        discount = ''
    docx = DocxTemplate(join(sample_folder, 'lease.docx'))
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
        'sum': str(round(contract["renta_price"] / 30.5, 1)),
        'payday': contract['pay_day'].astimezone(texas_tz).strftime('%#d'),
        'deposit': str(contract['zalog']),
        'limit': limit,
        'phone': phone,
        'address': check_value(contract, 'address'),
        'driving_license': check_value(contract, 'license', default='             '),
        'license_expiration': license_end,
        'state': check_value(contract, 'state', default='        '),
        'discount': discount
    }
    if not (add_sign and has_key(contract, 'email')):
        context['signature'] = '_____________'
    else:
        context['signature'] = '{{signature}}'
    docx.render(context)
    name = 'lease.docx'#f'LEASE-{contract_name}-{dt.now().strftime("%d-%m-%H-%M-%S")}.docx'
    docx.save(join(result_folder, name))
    print(f'lease build completed. Built contract: {contract_name}. Time: {round(time() - start_time, 2)} seconds.')
    return name

def lease_listener(db: client, bucket):
    """start lease listener

    Args:
        db (client): database
        bucket (bucket): firestore bucket
    """
    print('initialize lease listener.')

    def snapshot(document: list[document], changes, read_time):
        """snapshot the lease contract

        Args:
            document (list[document]): document
            changes ([type]): nothing
            read_time ([type]): nothing
        """
        try:
            doc = document[0].to_dict()
            add_sign = doc['add_sign']
            if doc['word_active']:
                print(f'write docx {doc["word_contract"]} (lease)')
                name = build(db, doc['word_contract'], add_sign)
                if '--read-only' not in argv:
                    blob = bucket.blob(f'word/{doc["word_contract"]}-{dt.now().strftime("%d-%m-%H-%M-%S")}.docx')
                    blob.upload_from_filename(join(result_folder, name))
                    blob.make_public()
                    print(f'write url to firestore: {blob.public_url}')
                else:
                    print('file not upload because of "--read-only" flag.')
                if '--read-only' not in argv:
                    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({
                        'word_active': False,
                        'word_url': blob.public_url, #f'http://nta.desicarscenter.com:8000/files/{name}'
                        'add_sign': False
                    })
                else:
                    print('word_active not reseted because of "--read-only" flag.')
                if add_sign:
                    contract = get_contract(db, doc['word_contract'], 'ContractName', False)
                    if has_key(contract, 'email'):
                        db.collection('Contract').document(contract['_firebase_document_id']).update({'document_status': 'sending'})
                        sign(contract['renter'], contract['email'], join(result_folder, name))
                        db.collection('Contract').document(contract['_firebase_document_id']).update({'document_status': 'sent'})

        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from lease snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)

if __name__ == '__main__':
    logdata.logfile('\n')
    run = ''
    for i in argv:
        run += i + ' '
    logdata.log_init(run)

    print('start subprocess lease.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--listener: activate lease listener')
        print('')
        print('default flags:')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this\
subprocess from watcher.py (use --lease-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('LEASE AGREEMENT')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--listener' in argv:
            lease_listener(db, bucket())
            while True:
                sleep(52)

    print('lease subprocess stopped successfully.')
