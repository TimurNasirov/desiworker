'''
OWNER REPORT
If somebody want to get owner reports from DesiCars app, this program will create owner file with all cars and these pays (incomes and expenses)
of chosen owner. This program will get all cars from db, get pay and toll data for cars, counting total income, and print it in excel file.
owner file will appear in firebase storage and its link will be in setting_app.
Activate:
 1. Choose start and end date (excel_start_date, excel_end_date) in setting_app.
 2. Choose owner (excel_owner) in setting app too.
 3. Change excel_active to True.
 4. Wait, and after few seconds link of owner file will appear in excel_url.


Collection: setting-app
Old name: excel
Group: exword
Launch time: - [exword] (snapshots only)
Marks: listener
'''

from sys import path, argv
from os.path import dirname, abspath, join
from os import get_terminal_size, _exit
from traceback import format_exception
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from openpyxl.styles import Font, Border, Side, Alignment
from openpyxl import Workbook
from rentacar.mods.firemod import has_key, client, init_db, document, bucket
from rentacar.mods.timemod import dt, sleep
from rentacar.str_config import SETTINGAPP_DOCUMENT_ID
from rentacar.log import Log
from requests import get
from config import TELEGRAM_LINK

logdata = Log('owner.py')
print = logdata.print

folder = join(dirname(dirname(abspath(__file__))), 'exword_results')

bold_font = Font(bold=True, name='Arial')
income_font = Font(color='00b121', name='Arial')
expense_font = Font(color='b12100', name='Arial')
income_bold_font = Font(color='00b121', bold=True, name='Arial')
expense_bold_font = Font(color='b12100', bold=True, name='Arial')
total_font = Font(color='007dc8', name='Arial')
invoice_font = Font(color='137cba', underline='single', name='Arial')

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
top_line = Border(
    top=Side(border_style='medium', color='000000')
)
right_line = Border(
    right=Side(border_style='medium', color='000000')
)
top_right_line = Border(
    top=Side(border_style='medium', color='000000'),
    right=Side(border_style='medium', color='000000')
)

class Work:
    """Payment (Work) class"""
    def __init__(self, date, work, amount, sum_, invoice=None, category='default'):
        """Initialize the object for the payment

        Args:
            date (str): date
            work (str): name of pay
            amount (str): amount of pay
            sum_ (float): pay summ
            invoice (str, optional): invoice of pay. Defaults to None.
        """
        self.date: str = date
        self.work: str = work
        self.amount: int = amount
        self.sum_: float = sum_
        self.invoice: str = invoice
        self.category: str = category

class Car:
    """A class for the Car class"""
    def __init__(self, name, work_income, work_expense):
        """Initialize the car class

        Args:
            name (str): car nickname
            work_income (list[Work]): incomes
            work_expense (list[Work]): expenses
        """
        self.name: str = name
        self.work_income: list[Work] = work_income
        self.work_expense: list[Work] = work_expense

    def get_subtotal(self, income: bool):
        """Get the subtotal of the car

        Args:
            income (bool): is need to calc incomes

        Returns:
            float: subtotal
        """
        subtotal = 0
        if income:
            for i in self.work_income:
                subtotal += i.sum_
        else:
            for i in self.work_expense:
                subtotal += i.sum_
        return subtotal

    def get_total(self):
        """Get the total from subtotal

        Returns:
            float: total
        """
        return self.get_subtotal(1) - self.get_subtotal(0)

class ExcelData:
    """Class to handle ExcelData objects"""
    def __init__(self, date, owner, cars):
        """Initialize the owner object

        Args:
            date (str): current date
            owner (str): owner of cars
            cars (list[Car]): cars list
        """
        self.date: str = date
        self.cars: list[Car] = cars
        self.owner: str = owner

    def get_subtotal(self):
        """Get the subtotal of all cars

        Returns:
            float: subtotal
        """
        subtotal = 0
        for i in self.cars:
            subtotal += i.get_total()
        return subtotal

    def get_percent(self, percent=20):
        """Returns the percentage of the current subtotal

        Args:
            percent (int, optional): percent. Defaults to 20.

        Returns:
            float: subtotal - percent
        """
        return self.get_subtotal() * percent / 100

    def get_total(self):
        """Get the total sum

        Returns:
            float: total
        """
        return self.get_subtotal() - self.get_percent()

def build(data: ExcelData):
    """Build a workbook from the data

    Args:
        data (ExcelData): data for build
    """
    wb = Workbook()
    ws = wb.active
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['J'].width = 10
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 19
    ws.freeze_panes = 'A7'

    for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', "J", 'K', 'L', 'M']:
        for j in ws[f'{i}1:{i}1000']:
            j[0].font = Font(name='Arial')
            j[0].alignment = Alignment(horizontal='center', vertical='center')

    ws['A1'].value = 'Period:'
    ws['A1'].font = bold_font
    if len(data.date.split('; ')) > 1:
        ws['B1'].value = data.date.split('; ')[0] + ' - ' +  data.date.split('; ')[-1]
    else:
        ws['B1'].value = data.date.split('; ')[0]
    ws['B1'].font = bold_font

    ws['D1'].value = 'Owner:'
    ws['D1'].font = bold_font
    ws['E1'].value = data.owner
    ws['E1'].font = bold_font

    ws['A2'].value = 'Expense'
    ws['A2'].border = short_border
    ws['B2'] = '=SUM(E:E)'
    ws['B2'].border = short_border
    ws['B2'].font = expense_font

    ws['A3'].value = 'Income'
    ws['A3'].border = short_border
    ws['B3'] = '=SUM(K:K)'
    ws['B3'].border = short_border
    ws['B3'].font = income_font

    ws['A4'].value = 'Service'
    ws['A4'].border = short_border
    ws['B4'] = '=SUM(L:L)'
    ws['B4'].border = short_border
    ws['C4'].value = '20%'
    ws['C4'].border = short_border

    ws['A5'].value = 'Total'
    ws['A5'].border = short_border
    ws['B5'] = '=SUM(M:M)'
    ws['B5'].border = short_border
    ws['B5'].font = total_font

    row = 7
    for i in data.cars:
        ws[f'A{row}'].border = top_line
        ws[f'B{row}'].border = top_line
        ws[f'C{row}'].border = top_line
        ws[f'D{row}'].border = top_line

        ws.merge_cells(f'E{row}:F{row}')
        ws[f'E{row}'].border = tall_border
        ws[f'E{row}'].value = i.name
        ws[f'F{row}'].border = tall_border

        ws[f'G{row}'].border = top_line
        ws[f'H{row}'].border = top_line
        ws[f'I{row}'].border = top_line
        ws[f'J{row}'].border = top_line
        ws[f'K{row}'].border = top_line
        ws[f'L{row}'].border = top_line

        length = max(len(i.work_expense), len(i.work_income)) + 6
        ws[f'M{row}'].border = top_right_line
        for j in range(row + 1, row + length + 1):
            ws[f'M{j}'].border = right_line

        ws[f'B{row + 1}'].value = 'Expense'
        ws[f'B{row + 1}'].font = expense_bold_font

        ws[f'A{row + 2}'].value = 'Date'
        ws[f'A{row + 2}'].border = tall_border
        ws[f'A{row + 2}'].font = bold_font

        ws[f'B{row + 2}'].value = 'Work'
        ws[f'B{row + 2}'].border = tall_border
        ws[f'B{row + 2}'].font = bold_font

        ws[f'C{row + 2}'].value = 'Amount'
        ws[f'C{row + 2}'].border = tall_border
        ws[f'C{row + 2}'].font = bold_font

        ws[f'D{row + 2}'].value = 'Sum'
        ws[f'D{row + 2}'].border = tall_border
        ws[f'D{row + 2}'].font = bold_font

        count = 0
        for j in i.work_expense:
            ws[f'A{row + 3 + count}'].value = j.date
            ws[f'A{row + 3 + count}'].border = short_border
            ws[f'B{row + 3 + count}'].value = j.work
            ws[f'B{row + 3 + count}'].border = short_border
            ws[f'C{row + 3 + count}'].value = j.amount
            ws[f'C{row + 3 + count}'].border = short_border
            ws[f'D{row + 3 + count}'].value = j.sum_
            ws[f'D{row + 3 + count}'].border = short_border

            if j.invoice:
                ws[f'E{row + 3 + count}'].value = 'Invoice'
                ws[f'E{row + 3 + count}'].hyperlink = j.invoice
                ws[f'E{row + 3 + count}'].font = invoice_font

            count += 1

        ws[f'D{row + length - 2}'].value = 'Subtotal:'
        ws[f'D{row + length - 2}'].font = bold_font

        ws[f'E{row + length - 2}'] = f'=SUM(D{row}:D{length + row})'
        ws[f'E{row + length - 2}'].font = expense_font


        ws[f'H{row + 1}'].value = 'Income'
        ws[f'H{row + 1}'].font = income_bold_font

        ws[f'G{row + 2}'].value = 'Date'
        ws[f'G{row + 2}'].border = tall_border
        ws[f'G{row + 2}'].font = bold_font

        ws[f'H{row + 2}'].value = 'Name'
        ws[f'H{row + 2}'].border = tall_border
        ws[f'H{row + 2}'].font = bold_font

        ws[f'I{row + 2}'].value = 'Amount'
        ws[f'I{row + 2}'].border = tall_border
        ws[f'I{row + 2}'].font = bold_font

        ws[f'J{row + 2}'].value = 'Sum'
        ws[f'J{row + 2}'].border = tall_border
        ws[f'J{row + 2}'].font = bold_font

        count = 0
        for j in i.work_income:
            ws[f'G{row + 3 + count}'].value = j.date
            ws[f'G{row + 3 + count}'].border = short_border
            ws[f'H{row + 3 + count}'].value = j.work
            ws[f'H{row + 3 + count}'].border = short_border
            ws[f'I{row + 3 + count}'].value = j.amount
            ws[f'I{row + 3 + count}'].border = short_border
            ws[f'J{row + 3 + count}'].value = j.sum_
            ws[f'J{row + 3 + count}'].border = short_border
            count += 1

        ws[f'J{row + length - 2}'].value = 'Subtotal:'
        ws[f'J{row + length - 2}'].font = bold_font

        ws[f'K{row + length - 2}'] = f'=SUM(J{row}:J{length + row})'
        ws[f'K{row + length - 2}'].font = income_font


        ws[f'K{row + length - 1}'].value = 'Service:'
        ws[f'K{row + length - 1}'].font = bold_font

        ws[f'L{row + length - 1}'] = f'=K{row + length - 2}*C4'
        ws[f'L{row + length - 1}'].font = expense_font


        ws[f'L{row + length - 2}'].value = 'Total:'
        ws[f'L{row + length - 2}'].font = bold_font

        ws[f'M{row + length - 2}'] = f'=K{row + length - 2}-L{row + length - 1}-E{row + length - 2}'
        ws[f'M{row + length - 2}'].font = total_font

        if i.name == data.cars[len(data.cars) - 1].name:
            for j in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']:
                ws[f'{j}{row + length + 1}'].border = top_line

        row += length

    wb.save(join(folder, 'owner.xlsx'))
    wb.close()


def get_data(date, owner, db):
    """Get all the data for a particular date

    Args:
        date (date): current date
        owner (str): owner of cars
        db (client): database

    Returns:
        ExcelData: data for build
    """
    doc = db.collection('Pay').get()
    pay_data = []
    for i in doc:
        pay_data.append(i.to_dict())

    doc = db.collection('Pay_contract').get()
    pay_contract_data = []
    for i in doc:
        pay_contract_data.append(i.to_dict())

    doc = db.collection('Repire').get()
    repire_data = []
    for i in doc:
        repire_data.append(i.to_dict())

    doc = db.collection('cars').get()
    cars = []
    for i in doc:
        data = i.to_dict()
        if 'owner' not in data.keys():
            continue
        if data['owner'] != owner:
            continue

        nick = data['nickname']
        incomes = []
        expenses = []
        for pay in pay_data:
            if pay['nickname'] == nick and pay['date'].strftime('%m.%Y') in date:
                amount = pay['amount'] if has_key(pay, 'amount') else 1
                invoice = None
                if has_key(pay, 'photo'):
                    if len(pay['photo']) > 0:
                        invoice = pay['photo'][-1]

                if has_key(pay, 'income'):
                    if pay['income']:
                        incomes.append(Work(pay['date'].strftime('%d.%m.%Y'), pay['name_pay'], amount, pay['sum'], invoice))
                if has_key(pay, 'expense'):
                    if pay['expense']:
                        expenses.append(Work(pay['date'].strftime('%d.%m.%Y'), pay['name_pay'], amount, pay['sum'], invoice))

        for pay_contract in pay_contract_data:
            if pay_contract['nickname'] == nick and pay_contract['date'].strftime('%m.%Y') in date:
                if has_key(pay_contract, 'owner'):
                    if not pay_contract['owner']:
                        continue
                else:
                    continue
                amount = pay_contract['amount'] if has_key(pay_contract, 'amount') else 1
                invoice = None
                if has_key(pay_contract, 'photo_pay'):
                    if len(pay_contract['photo_pay']) > 0:
                        invoice = pay_contract['photo_pay'][-1]

                category = 'default'
                if has_key(pay_contract, 'category'):
                    category = pay_contract['category']

                if has_key(pay_contract, 'expense'):
                    if pay_contract['expense']:
                        incomes.append(Work(pay_contract['date'].strftime('%d.%m.%Y'), pay_contract['name_pay'], amount, pay_contract['sum'], invoice, category))

        for repire in repire_data:
            if repire['nickname'] == nick and repire['date_time'].strftime('%m.%Y') in date:
                amount = repire['amount'] if has_key(repire, 'amount') else 1
                invoice = None
                if has_key(repire, 'photo'):
                    if len(repire['photo']) > 0:
                        invoice = repire['photo'][-1]

                if has_key(repire, 'expense'):
                    if repire['expense']:
                        expenses.append(Work(repire['date_time'].strftime('%d.%m.%Y'), repire['work_type'], amount, repire['sum'], invoice))

        daily_rents = 0
        daily_rents_sum = 0
        for income in incomes.copy():
            if income.category == 'daily rent':
                daily_rents += 1
                daily_rents_sum += int(income.sum_)
                incomes.remove(income)

        if daily_rents > 0:
            incomes.append(Work('-', 'Daily rent', daily_rents, daily_rents_sum, None, 'daily rent'))

        expenses.append(Work(f'01.{date[0]}', 'Bouncie', len(date), 8.53 * len(date)))
        cars.append(Car(nick, incomes, expenses))

    str_date = ''
    for i in date:
        if i == date[-1]:
            str_date += i
        else:
            str_date += i + '; '

    return ExcelData(str_date, owner, cars)


def get_range_periods(start_period, end_period):
    """Given a period between start and end preiods

    Args:
        start_period (str): start period
        end_period (str): end period

    Returns:
        str: period (thought comma)
    """
    range_periods = []
    last_period = start_period
    counter = 0
    while last_period != end_period:
        if counter != 0:
            splitted_period = last_period.split('.')
            if splitted_period[0] == '12':
                splitted_period[1] = str(int(splitted_period[1]) + 1)
                splitted_period[0] = '01'
            else:
                if splitted_period[0][0] == '0':
                    splitted_period[0] = splitted_period[0][1:len(splitted_period[0])]
                splitted_period[0] = str(int(splitted_period[0]) + 1)
                if len(splitted_period[0]) == 1:
                    splitted_period[0] = '0' + splitted_period[0]
                last_period = splitted_period[0] + '.' + splitted_period[1]
        if counter > 50:
            print('autokill executed')
            quit()
        range_periods.append(last_period)
        counter += 1
    if not range_periods:
        range_periods.append(end_period)
    return range_periods


def owner_listener(db: client, bucket):
    """Start the owner listener

    Args:
        db (client): databse
        bucket (bucket): bucket to upload data
    """
    print('initialize owner listener.')

    def snapshot(document: list[document], changes, read_time):
        """snapshot the document

        Args:
            document (list[document]): list of docuemnts
            changes: nothing
            read_time: nothing
        """
        try:
            doc = document[0].to_dict()

            if doc['excel_active']:
                print(f'write xlsx {doc["excel_owner"]} (owner)')

                periods = get_range_periods(doc["excel_start_date"].strftime('%m.%Y'), doc["excel_end_date"].strftime('%m.%Y'))
                data = get_data(periods, doc['excel_owner'], db)
                build(data)

                if '--read-only' not in argv:
                    blob = bucket.blob(f'excel/{doc["excel_owner"]}-{dt.now().strftime("%d-%m-%H-%M-%S")}.xlsx')
                    blob.upload_from_filename(join(folder, 'owner.xlsx'))
                    blob.make_public()
                    print(f'write url to firestore: {blob.public_url}')
                else:
                    print('file not upload because of "--read-only" flag.')

                if '--read-only' not in argv:
                    db.collection('setting_app').document(SETTINGAPP_DOCUMENT_ID).update({'excel_active': False, 'excel_url': blob.public_url})
                else:
                    print('excel_active not reseted because of "--read-only" flag.')

        except Exception as e:
            exc_data = format_exception(e)[-2].split('\n')[0]
            line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
            module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
            print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}). [from owner snapshot]')
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

    print('start subprocess owner.')
    if len(argv) == 1:
        print('not enough arguments.')
        print('add -h to arguments to get help.')

    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 55) // 2)} SUBPROCESS INSRUCTIONS {" " * ((size - 55) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('--listener: activate owner listener')
        print('')
        print('default flags:')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
        print('WARNING: catching errors not work in subprocess, so if error raising you will see full stacktrace. To fix it, run this subproces\
s from watcher.py (use --owner-only -t)')
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
            owner_listener(db, bucket())
            while True:
                sleep(52)

    print('owner subprocess stopped successfully.')
