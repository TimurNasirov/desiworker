"""
SUPA DESI
Copy all data from firebase collections to supabase.

Collection: *
Group: supadesi
Launch time: 23:57 [supadesi]
Marks: supabase
"""
from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size
from random import randint


from rentacar.mods.timemod import time, sleep, dt
from rentacar.mods.firemod import client, init_db
from rentacar.log import Log
from supabase import create_client
from rentacar.config import SUPABASE_URL, SUPABASE_KEY

logdata = Log('supadesi.py')
print = logdata.print
db = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_data(data: list, table: str) -> None:
    start = time()
    if '--read-only' not in argv:
        db.table(table).delete().gt('id', 0).execute()
        db.table(table).insert(data).execute()
    else:
        print('Table not updated because of "--read-only" flag.')
    #docs_resp = db.table(table).select('id').execute()
    # docs = []
    # for i in docs_resp.data:
    #     docs.append(i['documentId'])
    # for i in data:
    #     if i['documentId'] in docs:
    #         print(f'update {table} {i["documentId"]}')
    #         db.table(table).update(i).eq('documentId', i['documentId']).execute()
    #     else:
    #         print(f'create {table} {i["documentId"]}')
    #         db.table(table).insert(i).execute()
    end = time()
    print(f'Successfully updated {len(data)} rows. Time: {round(end - start, 2)} seconds')

def start_supadesi(db) -> None:
    reads = 0
    start_time = time()
    print('Get Contract table.')
    contract = db.collection('Contract').get()
    reads += len(contract)
    data2 = []
    for i in contract:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling contract {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('id')
        except KeyError: pass
        try: data['begin_time'] = data['begin_time'].isoformat()
        except KeyError: pass
        try: data['Comment_data'] = data['Comment_data'].isoformat()
        except KeyError: pass
        try: data['end_time'] = data['end_time'].isoformat()
        except KeyError: pass
        try: data['Insurance_end'] = data['Insurance_end'].isoformat()
        except KeyError: pass
        try: data['licenseDate'] = data['licenseDate'].isoformat()
        except KeyError: pass
        try: data['pay_day'] = data['pay_day'].isoformat()
        except KeyError: pass
        try: data['last_payday'] = data['last_payday'].isoformat()
        except KeyError: pass
        try:
            commentDate = []
            for i in data['commentDate']:
                commentDate.append(i.isoformat())
            data['commentDate'] = commentDate
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Contract')

    print('Get Contract.ContractComment table.')
    comments = db.collection_group('ContractComment').get()
    reads += len(comments)
    data2 = []
    for i in comments:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling comments {data["documentId"]}')
        # sleep(0.01)
        data['parentDocumentId'] = i.reference.parent.parent.id
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        try: data.pop('ID')
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Contract.ContractComment')

    print('Get Contract.Promo table.')
    comments = db.collection_group('Promo').get()
    reads += len(comments)
    data2 = []
    for i in comments:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling comments {data["documentId"]}')
        # sleep(0.01)
        data['parentDocumentId'] = i.reference.parent.parent.id
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Contract.Promo')

    print('Get History table.')
    history = db.collection('History').get()
    reads += len(history)
    data2 = []
    for i in history:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling history {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('id')
        except KeyError: pass
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'History')

    print('Get Last_update_python table.')
    last_update = db.collection('Last_update_python').document('last_update').get()
    reads += 1
    data = last_update.to_dict()
    data2 = [
        {'name': 'toll', 'date': data['toll_update'].isoformat()},
        {'name': 'odometer', 'date': data['odometer_update'].isoformat()},
        {'name': 'payday', 'date': data['payday_update'].isoformat()},
        {'name': 'insurance', 'date': data['insurance_update'].isoformat()},
        {'name': 'post', 'date': data['post_update'].isoformat()},
        {'name': 'changeoil', 'date': data['changeoil_update'].isoformat()},
        {'name': 'registration', 'date': data['registration_update'].isoformat()},
        {'name': 'saldo', 'date': data['saldo_update'].isoformat()},
        {'name': 'paylimit', 'date': data['paylimit_update'].isoformat()},
        {'name': 'payevery', 'date': data['payevery_update'].isoformat()},
    ]
    add_data(data2, 'last_update')

    print('Get Owner table.')
    owner = db.collection('Owner').get()
    reads += len(owner)
    data2 = []
    for i in owner:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling owner {data["documentId"]}')
        # sleep(0.01)
        data2.append(data)
    add_data(data2, 'Owner')

    print('Get Pay table.')
    pay = db.collection('Pay').get()
    reads += len(pay)
    data2 = []
    for i in pay:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling pay {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('id')
        except KeyError: pass
        if 'delete' not in data.keys():
            data['delete'] = False
        if 'income' not in data.keys():
            data['income'] = False
        if 'expense' not in data.keys():
            data['expense'] = False
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Pay')

    print('Get Pay_contract table.')
    pay_contract = db.collection('Pay_contract').get()
    reads += len(pay_contract)
    data2 = []
    for i in pay_contract:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling pay_contract {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('id')
        except KeyError: pass
        if 'delete' not in data.keys():
            data['delete'] = False
        if 'income' not in data.keys():
            data['income'] = False
        if 'expense' not in data.keys():
            data['expense'] = False
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Pay_contract')

    print('Get Repire table.')
    repire = db.collection('Repire').get()
    reads += len(repire)
    data2 = []
    for i in repire:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling repire {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('id')
        except KeyError: pass
        if 'delete' not in data.keys():
            data['delete'] = False
        if 'income' not in data.keys():
            data['income'] = False
        if 'expense' not in data.keys():
            data['expense'] = False
        try: data['date_time'] = data['date_time'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Repire')

    print('Get Task table.')
    task = db.collection('Task').get()
    reads += len(task)
    data2 = []
    for i in task:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling task {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('id')
        except KeyError: pass
        if 'post' not in data.keys():
            data['post'] = False
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        try: data['post_time'] = data['post_time'].isoformat()
        except KeyError: pass
        try: data['task_close'] = data['task_close'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Task')

    print('Get Task.Parts table.')
    parts = db.collection_group('Parts').get()
    reads += len(parts)
    data2 = []
    for i in parts:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling parts {data["documentId"]}')
        # sleep(0.01)
        data['parentDocumentId'] = i.reference.parent.parent.id
        try: data.pop('ID')
        except KeyError: pass
        data2.append(data)

    add_data(data2, 'Task.Parts')

    print('Get Toll table.')
    toll = db.collection('Toll').get()
    reads += len(toll)
    data2 = []
    for i in toll:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling toll {data["documentId"]}')
        # sleep(0.01)
        try: data['transaction_id'] = data['ID']
        except KeyError: pass
        try: data.pop('ID')
        except KeyError: pass
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'Toll')

    print('Get auth_user table.')
    auth_user = db.collection('auth_user').get()
    reads += len(auth_user)
    data2 = []
    for i in auth_user:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling user {data["documentId"]}')
        data2.append(data)
    add_data(data2, 'auth_user')

    print('Get cars table.')
    cars = db.collection('cars').get()
    reads += len(cars)
    data2 = []
    for i in cars:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling car {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('id')
        except KeyError: pass
        try: data['TO_end'] = data['TO_end'].isoformat()
        except KeyError: pass
        try: data['last_time'] = data['last_time'].isoformat()
        except KeyError: pass
        ##print('handling list<datetime> into list<timestamp>')
        try:
            commentDate = []
            for i in data['commentDate']:
                commentDate.append(i.isoformat())
            data['commentDate'] = commentDate
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'cars')

    print('Get inspection table.')
    inspection = db.collection('inspection').get()
    reads += len(inspection)
    data2 = []
    for i in inspection:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling inspection {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('ID')
        except KeyError: pass
        try: data['date'] = data['date'].isoformat()
        except KeyError: pass
        try: data['registration'] = data['registration'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'inspection')

    print('Get setting_app table.')
    setting_app = db.collection('setting_app').document('Mo7VMvpoEdLB7ao9XnAo').get()
    data = setting_app.to_dict()
    reads += 1
    if not data:
        print('error: incorrect data')
        quit()
    try: data['excel_start_date'] = data['excel_start_date'].isoformat()
    except KeyError: pass
    try: data['excel_end_date'] = data['excel_end_date'].isoformat()
    except KeyError: pass
    try: data['incomes_start_date'] = data['incomes_start_date'].isoformat()
    except KeyError: pass
    try: data['incomes_end_date'] = data['incomes_end_date'].isoformat()
    except KeyError: pass
    add_data(data, 'setting_app')

    print('Get Temp_APP table.')
    temp_app = db.collection('Temp_APP').document('vPHKtqC5mppukNZWplBl').get()
    data = temp_app.to_dict()
    reads += 1
    if not data:
        print('error: incorrect data')
        quit()
    add_data(data, 'Temp_APP')

    print('Get InboxSMS table.')
    inboxsms = db.collection('InboxSMS').get()
    reads += len(inboxsms)
    data2 = []
    for i in inboxsms:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling inboxsms {data["documentId"]}')
        # sleep(0.01)
        try: data.pop('ID')
        except KeyError: pass
        try: data['created_time'] = data['created_time'].isoformat()
        except KeyError: pass
        try: data['changed_time'] = data['changed_time'].isoformat()
        except KeyError: pass
        data2.append(data)
    add_data(data2, 'InboxSMS')

    print('Get InboxSMS.messages table.')
    messages = db.collection_group('messages').get()
    reads += len(messages)
    data2 = []
    for i in messages:
        data = i.to_dict()
        data['documentId'] = i.id
        #print(f'handling messages {data["documentId"]}')
        # sleep(0.01)
        data['parentDocumentId'] = i.reference.parent.parent.id
        try: data.pop('ID')
        except KeyError: pass
        try: data['created_time'] = data['created_time'].isoformat()
        except KeyError: pass
        try: data['readed_time'] = data['readed_time'].isoformat()
        except KeyError: pass
        data2.append(data)
        if 'type' not in data.keys():
            data['type'] = 'chat'
    add_data(data2, 'InboxSMS.messages')
    total_time = round(time() - start_time, 2)
    print(f'Supadesi work completed. Time: {total_time} seconds. Reads: {reads}')
