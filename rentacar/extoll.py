'''
TOLL REPORT
If somebody want to get toll reports from DesiCars app, this program will create file with all tolls of chosen car (plate). This
program will get all tolls that arrived from this plate, counting total expense, and print it in excel file.
extoll file will appear in firebase storage and its link will be in setting_app.
Activate:
 1. Choose plate of car (toll_plate) in setting app.
 2. Change toll_active to True.
 3. Wait, and after few seconds link of extoll file will appear in toll_url.


Collection: setting-app
Old name: toll
Group: exword
Launch time: - [exword] (snapshots only)
Marks: listener, excel
'''

from sys import path, argv
from os.path import dirname, abspath, join
from os import get_terminal_size, _exit
from traceback import format_exception
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from openpyxl.styles import Border, Side, Font, Alignment
from openpyxl import Workbook
from rentacar.mods.firemod import has_key, client, init_db, document, bucket, to_dict_all
from rentacar.mods.timemod import dt, sleep
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.log import Log
from requests import get
from config import TELEGRAM_LINK

logdata = Log('extoll.py')
print = logdata.print
folder = '/rentacar/exword_results/' if '-d' in argv else join(dirname(abspath(__file__)), 'exword_results')

short_border = Border(
    left=Side(border_style='thin', color='000000'),
    top=Side(border_style='thin', color='000000'),
    bottom=Side(border_style='thin', color='000000'),
    right=Side(border_style='thin', color='000000')
)
tall_border = Border(
    left=Side(border_style='medium', color='000000'),
    top=Side(border_style='medium', color='000000'),
    bottom=Side(border_style='medium', color='000000'),
    right=Side(border_style='medium', color='000000')
)

class Toll:
    """toll class"""
    def __init__(self, _id, location, _sum, _type, date):
        """initialize toll class

        Args:
            _id (int): toll id
            location (str): location
            _sum (float): summ
            _type (str): transaction type
            date (str): date
        """
        self._id: int = _id
        self.location: str = location
        self._sum: float = _sum
        self._type: str = _type
        self.date = date


def build(data, nickname, plate):
    """build extoll excel file

    Args:
        data (list): tolls
        nickname (str): nickname
        plate (str): plate
    """
    wb = Workbook()
    ws = wb.active
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['C'].width = 16
    ws.column_dimensions['D'].width = 60
    ws.column_dimensions['E'].width = 8

    for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', "J", 'K', 'L', 'M']:
        for j in ws[f'{i}1:{i}1000']:
            j[0].font = Font(name='Arial', size=10)
            j[0].alignment = Alignment(horizontal='center', vertical='center')

    ws['A1'].value = 'ID'
    ws['A1'].border = tall_border

    ws['B1'].value = 'Type'
    ws['B1'].border = tall_border

    ws['C1'].value = 'Date'
    ws['C1'].border = tall_border

    ws['D1'].value = 'Location'
    ws['D1'].border = tall_border

    ws['E1'].value = 'Sum'
    ws['E1'].border = tall_border


    ws['G2'].value = 'Nickname'
    ws['G2'].border = tall_border

    ws['H2'].value = nickname
    ws['H2'].border = short_border

    ws['G3'].value = 'Plate'
    ws['G3'].border = tall_border

    ws['H3'].value = plate
    ws['H3'].border = short_border

    ws['G4'].value = 'Total'
    ws['G4'].border = tall_border

    ws['H4'].value = '=SUM(E:E)'
    ws['H4'].border = short_border

    row = 2
    for i in data:
        ws[f'A{row}'].value = i._id
        ws[f'A{row}'].border = short_border

        ws[f'B{row}'].value = i._type
        ws[f'B{row}'].border = short_border

        ws[f'C{row}'].value = i.date.strftime('%d.%m.%Y %H:%M')
        ws[f'C{row}'].border = short_border

        ws[f'D{row}'].value = i.location
        ws[f'D{row}'].border = short_border
        ws[f'D{row}'].font = Font(size=8, name='Arial')

        ws[f'E{row}'].value = i._sum
        ws[f'E{row}'].border = short_border

        row += 1

    name = 'extoll.xlsx'#f'EXTOLL-{plate}-{dt.now().strftime("%d-%m-%H-%M-%S")}.xlsx'
    wb.save(join(folder, name))
    wb.close()
    return name


def get_data(plate: str, db: client):
    """get toll data

    Args:
        plate (str): plate
        db (client): database

    Returns:
        list: data
    """
    toll_dict = to_dict_all(db.collection('Pay_contract').get())
    tolls = []
    for toll in toll_dict:
        if has_key(toll, 'category') and has_key(toll, 'plate'):
            if toll['category'] == 'toll' and toll['plate'] == plate:
                tolls.append(toll)

    tollclasses = []
    for toll in tolls:
        tollclasses.append(Toll(toll['id'], toll['comment'][9:toll['comment'].find(', type: ')], toll['sum'], toll['comment'][toll['comment'].find(', type: ') + 8:len(toll['comment'])], toll['date']))

    if len(tolls) > 0:
        return [tollclasses, tolls[-1]['nickname'] if 'nickname' in tolls[-1].keys() else '']
    else:
        return [[], '']

def extoll_listener(db: client, bucket):
    """start extoll listener

    Args:
        db (client): database
        bucket (bucket): bucket
    """
    print('initalize extoll listener.')
    def snapshot(document: list[document], changes, read_time):
        """handle extoll snapshot

        Args:
            document (list[document]): documents
            changes: nothing
            read_time: nothing
        """
        try:
            doc = document[0].to_dict()
            if doc['toll_active']:
                plate = doc['toll_plate']
                print(f'write xlsx {plate} (extoll)')
                data = get_data(plate, db)
                name = build(data[0], data[1], plate)
                if '--read-only' not in argv:
                    blob = bucket.blob(f'excel/{plate}-{dt.now().strftime("%d-%m-%H-%M-%S")}.xlsx')
                    blob.upload_from_filename(join(folder, name))
                    blob.make_public()
                    print(f'write url to firestore: {blob.public_url}')
                else:
                    print('file not upload because of "--read-only" flag')
                if '--read-only' not in argv:
                    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({
                        'toll_active': False,
                        'toll_url': blob.public_url#f'http://nta.desicarscenter.com:8000/files/{name}'
                    })
                else:
                    print('toll_active not reseted because of "--read-only" flag.')
        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from extoll snapshot]')
            get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

    doc = db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)


if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess extoll.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--listener: activate extoll listener')
        print('')
        print('default flags:')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --extoll-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('TOLL REPORT')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--listener' in argv:
            extoll_listener(db, bucket())
            while True:
                sleep(52)

    print('extoll subprocess stopped successfully.')
