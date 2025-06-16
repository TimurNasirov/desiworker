from sys import path, argv
from os.path import dirname, abspath, join
from os import get_terminal_size, _exit
from traceback import format_exception
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from rentacar.mods.firemod import has_key, client, init_db, document, bucket, get_contract
from rentacar.mods.timemod import dt, sleep, time
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.log import Log
from requests import get
from config import TELEGRAM_LINK

logdata = Log('card.py')
print = logdata.print

result_folder = '/rentacar/exword_results/' if '-d' in argv else join(dirname(abspath(__file__)), 'exword_results')
sample_folder = '/rentacar/exword_samples/' if '-d' in argv else join(dirname(abspath(__file__)), 'exword_samples')

def build(data: dict):
    start_time = time()
    docx = DocxTemplate(join(sample_folder, 'card.docx'))
    context = {
        'name': data['renter'] if has_key(data, 'renter') else '-',
        'address': data['address'] if has_key(data, 'address') else '-',
        'ins_number': data['insurance_number'] if has_key(data, 'insurance_number') else '-',
        'insurance': data['insurance'] if has_key(data, 'insurance') else '-',
        'ins_end': data['Insurance_end'].strftime('%Y.%m.%d') if has_key(data, 'Insurance_end') else '-',
        'lic_number': data['license'] if has_key(data, 'license') else '-',
        'lic_end': data['licenseDate'].strftime('%Y.%m.%d') if has_key(data, 'licenseDate') else '-',
        'state': data['state'] if has_key(data, 'state') else '-',
        'phone': data['renternumber'][0] + '                    ' if has_key(data, 'renternumber') else '-',
        'images': [InlineImage(docx, image, height=Mm(120)) for image in data['images']]
    }
    docx.render(context)
    name = 'card.docx'#f'CARD-{contract_name}-{dt.now().strftime("%d-%m-%H-%M-%S")}.docx'
    docx.save(join(result_folder, name))
    print(f'card build completed. Built contract: {data["ContractName"]}. Time: {round(time() - start_time, 2)} seconds.')
    return name

def get_data(db: client, contract_name: str):
    contract = get_contract(db, contract_name, 'ContractName', check_active=False)
    images = []
    index = 0
    for photo in contract['DocumentPhoto']:
        with open(f'card_images/{index}.png', 'wb') as fl:
            fl.write(get(photo).content)
        images.append(f'card_images/{index}.png')
        index += 1
    contract['images'] = images
    return contract

def card_listener(db: client, bucket):
    print('initialize card listener.')

    def snapshot(document: list[document], changes, read_time):
        try:
            doc = document[0].to_dict()
            if doc['card_active']:
                print(f'write docx {doc["card_contract"]} (card)')
                name = build(get_data(db, doc['card_contract']))
                if '--read-only' not in argv:
                    blob = bucket.blob(f'word/{doc["card_contract"]}-{dt.now().strftime("%d-%m-%H-%M-%S")}.docx')
                    blob.upload_from_filename(join(result_folder, name))
                    blob.make_public()
                    print(f'write url to firestore: {blob.public_url}')
                else:
                    print('file not upload because of "--read-only" flag.')
                if '--read-only' not in argv:
                    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({
                        'card_active': False,
                        'card_url': blob.public_url #f'http://nta.desicarscenter.com:8000/files/{name}'
                    })
                else:
                    print('card_active not reseted because of "--read-only" flag.')

        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from card snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)

if __name__ == '__main__':
    logdata.logfile('\n')
    run = ''
    for i in argv:
        run += i + ' '
    logdata.log_init(run)

    print('start subprocess card.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--listener: activate card listener')
        print('')
        print('default flags:')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this\
subprocess from watcher.py (use --card-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('RENTER CARD')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--listener' in argv:
            card_listener(db, bucket())
            while True:
                sleep(52)

    print('card subprocess stopped successfully.')
