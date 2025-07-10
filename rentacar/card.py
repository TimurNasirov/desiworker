"""
card.py
=======

Generates a Word document with renter and insurance information, including images, and uploads it
to the cloud.

Functions
------------
• **Builds a DOCX file from template**
  - Uses `docxtpl` to fill a Word template (`card.docx`) with contract and renter data:
    - Name, address, phone number
    - Insurance number and expiration
    - License number and expiration
    - State and photo images

• **Downloads document photos**
  - Loads renter’s document images (from Firestore URLs) and saves them locally for insertion into
the Word file.

• **Uploads result to cloud storage**
  - If not in `--read-only` mode, uploads the generated `.docx` to the bucket under the `word/`
folder with a timestamped filename.

• **Updates Firestore setting document**
  - Resets the flag `card_active` to `False`
  - Sets the `card_url` to the uploaded document's public link

• **Listens for trigger**
  - Uses Firestore listener on `setting_app/card_active == true`
  - Automatically reacts when a card document needs to be created

Flags
-----
`--read-only`
    Prevents file upload and database update. Used for testing or dry runs.

`-d`
    Switches to docker folder paths (`/rentacar/exword_results/`, `/rentacar/exword_samples/`).

linitng: 9.68
"""
from sys import argv
from os.path import dirname, abspath, join
from os import _exit
from traceback import format_exception
from typing import Literal

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from requests import get

from rentacar.config import TELEGRAM_LINK
from rentacar.mods.firemod import has_key, get_contract
from rentacar.mods.timemod import dt, time, texas_tz
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.log import Log

logdata = Log('card.py')
print = logdata.print

result_folder = '/rentacar/exword_results/' if '-d' in argv else join(dirname(abspath(__file__)),
    'exword_results')
sample_folder = '/rentacar/exword_samples/' if '-d' in argv else join(dirname(abspath(__file__)),
    'exword_samples')

def build(data: dict) -> Literal['card.docx']:
    """Builds the `card.docx` file from the given data and saves it locally."""
    start_time = time()
    docx = DocxTemplate(join(sample_folder, 'card.docx'))
    context = {
        'name': data['renter'] if has_key(data, 'renter') else '-',
        'address': data['address'] if has_key(data, 'address') else '-',
        'ins_number': data['insurance_number'] if has_key(data, 'insurance_number') else '-',
        'insurance': data['insurance'] if has_key(data, 'insurance') else '-',
        'ins_end': data['Insurance_end'].strftime('%Y.%m.%d') if has_key(data, 'Insurance_end')
            else '-',
        'lic_number': data['license'] if has_key(data, 'license') else '-',
        'lic_end': data['licenseDate'].strftime('%Y.%m.%d') if has_key(data, 'licenseDate')
            else '-',
        'state': data['state'] if has_key(data, 'state') else '-',
        'phone': data['renternumber'][0] + '                    ' if has_key(data, 'renternumber')
            else '-',
        'images': [InlineImage(docx, image, height=Mm(120)) for image in data['images']]
    }
    docx.render(context)
    name = 'card.docx'#f'CARD-{contract_name}-{dt.now(texas_tz).strftime("%d-%m-%H-%M-%S")}.docx'
    docx.save(join(result_folder, name))
    print(f'card build completed. Built contract: {data["ContractName"]}. Time:\
        {round(time() - start_time, 2)} seconds.')
    return name

def get_data(db, contract_name: str) -> dict:
    """Retrieves contract data and downloads all associated document images."""
    contract = get_contract(db, contract_name, 'ContractName', check_active=False)
    images = []
    index = 0
    for photo in contract['DocumentPhoto']:
        with open(f'card_images/{index}.png', 'wb') as fl:
            fl.write(get(photo, timeout=10).content)
        images.append(f'card_images/{index}.png')
        index += 1
    contract['images'] = images
    return contract

def card_listener(db, bucket) -> None:
    """Subscribes to changes on the `setting_app` document and handles document generation/upload.
    """
    print('initialize card listener.')

    def snapshot(document, _, __) -> None:
        try:
            doc = document[0].to_dict()
            if not doc:
                raise ValueError('doc is null')
            if doc['card_active']:
                print(f'write docx {doc["card_contract"]} (card)')
                name = build(get_data(db, doc['card_contract']))
                if '--read-only' not in argv:
                    blob = bucket.blob(f'word/{doc["card_contract"]}-\
{dt.now(texas_tz).strftime("%d-%m-%H-%M-%S")}.docx')

                    blob.upload_from_filename(join(result_folder, name))
                    blob.make_public()
                    print(f'write url to firestore: {blob.public_url}')

                    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({
                        'card_active': False,
                        'card_url': blob.public_url
                    })
                else:
                    print('file not uploaded and Firestore not updated because of "--read-only"\
flag.')
        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}).\
[from card snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module}\
({e.__class__.__name__})', timeout=10)
            _exit(1)

    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)
