from sys import path, argv
from os.path import dirname, abspath, join
from os import get_terminal_size, _exit
from traceback import format_exception
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from openpyxl.styles import Font, Border, Side, Alignment
from openpyxl import Workbook
from rentacar.mods.firemod import has_key, client, init_db, document, bucket, to_dict_all, get_car
from rentacar.mods.timemod import dt, sleep, texas_tz
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.log import Log
from requests import get
from config import TELEGRAM_LINK

logdata = Log('debt.py')
print = logdata.print

folder = '/rentacar/exword_results/' if '-d' in argv else join(dirname(abspath(__file__)), 'exword_results')

bold_font = Font(bold=True, name='Arial')
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

class Item:
    def __init__(self, name: str, rent: float, toll: float, extra: float, other: float, owner: str):
        self.name = name
        self.rent = rent
        self.toll = toll
        self.extra = extra
        self.other = other
        self.summ = rent + toll + extra + other
        self.owner = owner

def get_data(db: client, owner: str):
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    pay_contracts: list[dict] = to_dict_all(db.collection('Pay_contract').get())
    items: list[Item] = []

    for contract in contracts:
        if not contract['Active']:
            continue
        car = [car for car in cars if car['nickname'] == contract['nickname']][0]
        if car['owner'] != owner and owner != 'all':
            continue
        rent = 0
        toll = 0
        extra = 0
        other = 0

        for pay_contract in pay_contracts:
            if not has_key(pay_contract, 'ContractName'):
                continue
            if has_key(pay_contract, 'delete'):
                if pay_contract['delete']:
                    continue

            if pay_contract['ContractName'] == contract['ContractName']:
                if has_key(pay_contract, 'category'):
                    if pay_contract['category'] == 'daily rent':
                        if has_key(pay_contract, 'income'):
                            if pay_contract['income']: rent += pay_contract['sum']
                        if has_key(pay_contract, 'expense'):
                            if pay_contract['expense']: rent -= pay_contract['sum']
                    elif pay_contract['category'] == 'toll':
                        if has_key(pay_contract, 'income'):
                            if pay_contract['income']: toll += pay_contract['sum']
                        if has_key(pay_contract, 'expense'):
                            if pay_contract['expense']: toll -= pay_contract['sum']
                    elif pay_contract['category'] == 'extra':
                        if has_key(pay_contract, 'income'):
                            if pay_contract['income']: extra += pay_contract['sum']
                        if has_key(pay_contract, 'expense'):
                            if pay_contract['expense']: extra -= pay_contract['sum']
                    else:
                        if has_key(pay_contract, 'income'):
                            if pay_contract['income']: other += pay_contract['sum']
                        if has_key(pay_contract, 'expense'):
                            if pay_contract['expense']: other -= pay_contract['sum']
                else:
                    if has_key(pay_contract, 'income'):
                        if pay_contract['income']: other += pay_contract['sum']
                    if has_key(pay_contract, 'expense'):
                        if pay_contract['expense']: other -= pay_contract['sum']

        items.append(Item(contract['ContractName'], round(rent, 2), round(toll, 2), round(extra, 2), round(other, 2), car['owner']))

    items.sort(key=lambda item: item.summ)
    return items


def build(data: list[Item]):
    wb = Workbook()
    ws = wb.active
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['F'].width = 17

    for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', "J", 'K', 'L', 'M']:
        for j in ws[f'{i}1:{i}1000']:
            j[0].font = Font(name='Arial')
            j[0].alignment = Alignment(horizontal='center', vertical='center')

    ws['A1'].value = 'Contract name'
    ws['A1'].font = bold_font
    ws['A1'].border = tall_border

    ws['B1'].value = 'Rent'
    ws['B1'].font = bold_font
    ws['B1'].border = tall_border

    ws['C1'].value = 'Toll'
    ws['C1'].font = bold_font
    ws['C1'].border = tall_border

    ws['D1'].value = 'Extra'
    ws['D1'].font = bold_font
    ws['D1'].border = tall_border

    ws['E1'].value = 'Other'
    ws['E1'].font = bold_font
    ws['E1'].border = tall_border

    ws['F1'].value = 'Balance'
    ws['F1'].font = bold_font
    ws['F1'].border = tall_border

    ws['G1'].value = 'Owner'
    ws['G1'].font = bold_font
    ws['G1'].border = tall_border

    row = 2
    for item in data:
        ws[f'A{row}'].value = item.name
        ws[f'A{row}'].border = short_border

        ws[f'B{row}'].value = item.rent
        ws[f'B{row}'].border = short_border

        ws[f'C{row}'].value = item.toll
        ws[f'C{row}'].border = short_border

        ws[f'D{row}'].value = item.extra
        ws[f'D{row}'].border = short_border

        ws[f'E{row}'].value = item.other
        ws[f'E{row}'].border = short_border

        ws[f'F{row}'].value = item.summ
        ws[f'F{row}'].border = short_border

        ws[f'G{row}'].value = item.owner
        ws[f'G{row}'].border = short_border

        row += 1

    name = 'debt.xlsx'#f'DEBT-{data.owner}-{dt.now(texas_tz).strftime("%d-%m-%H-%M-%S")}.xlsx'
    wb.save(join(folder, name))
    wb.close()
    return name


def debt_listener(db: client, bucket):
    """Start the debt listener

    Args:
        db (client): databse
        bucket (bucket): bucket to upload data
    """
    print('initialize debt listener.')

    def snapshot(document: list[document], changes, read_time):
        """snapshot the document

        Args:
            document (list[document]): list of docuemnts
            changes: nothing
            read_time: nothing
        """
        try:
            doc = document[0].to_dict()

            if doc['debt_active']:
                print(f'write xlsx {doc["debt_owner"]} (debtreport)')
                name = build(get_data(db, doc['debt_owner']))

                if '--read-only' not in argv:
                    blob = bucket.blob(f'excel/debt-{dt.now(texas_tz).strftime("%d-%m-%H-%M-%S")}.xlsx')
                    blob.upload_from_filename(join(folder, name))
                    blob.make_public()
                    print(f'write url to firestore: {blob.public_url}')
                else:
                    print('file not upload because of "--read-only" flag.')

                if '--read-only' not in argv:
                    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({
                        'debt_active': False,
                        'debt_url': blob.public_url #f'http://nta.desicarscenter.com:8000/files/{name}'
                    })
                else:
                    print('debt_active not reseted because of "--read-only" flag.')

        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from debtreport snapshot]')
            if '--no-tg' not in argv:
                get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')
            _exit(1)

        except KeyboardInterrupt:
            print('main process stopped.')
    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).on_snapshot(snapshot)


if __name__ == '__main__':
    logdata.logfile('\n')
    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    print('start subprocess debt.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--listener: activate debt listener')
        print('')
        print('default flags:')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --debt-only -t)')
        print('')
        print('Description:')
        instruction = __doc__.split('\n')
        instruction.remove('')
        instruction.remove('OWNER REPORT')
        for i in instruction:
            print(i)
    else:
        db: client = init_db()
        if '--listener' in argv:
            debt_listener(db, bucket())
            while True:
                sleep(52)

    print('debt subprocess stopped successfully.')
