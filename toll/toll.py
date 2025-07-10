"""
When renter is driving thought toll road or park in paid place, NTTA system get this data and
publish it on their site. This program take this data from their website and add it in firebase
collection Toll. After that owner can see about renter need to pay for this because NTTA
automaticly get money from owner and pay for this paid things. Often, renter pay for paid things
when today is pay day.
TOLL
Collection: Toll
Group: toll
Launch time: 23:45, 12:10 [toll]
Marks: last-update, selenium
"""
from sys import path, argv
from os.path import dirname, abspath
from os import remove
from csv import reader
from log import Log

from mods.firemod import to_dict_all, get_car, has_key, get_contract, FieldFilter
from mods.timemod import sleep, dt, timedelta, texas_tz
from rentacar.config import NTTA_URL, NTTA_LOGIN, NTTA_PASSWORD, NTTA_HISTORY_URL
from str_config import TOLL_USERNAME_ID, TOLL_PASSWORD_NAME, TOLL_LOGIN_BUTTON_SELECTOR,\
    TOLL_CSV_XPATH, TOLL_FILENAME, USER, TOLL_CATEGORY, TOLL_COMMENT_TASK, TOLL_NAME_PAY,\
    TOLL_NAME_TASK, TOLL_COMMENT_PAY, TOLL_DOWNLOAD_PATH

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC




logdata = Log('toll.py')
print = logdata.print

def start_toll(db) -> None:
    """start toll"""
    print('start toll.')
    #download.py
    options = Options()
    # options.add_argument('--no-sandbox')
    # options.add_argument('--headless')
    if '-d' in argv:
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("prefs", {
            "download.default_directory": TOLL_DOWNLOAD_PATH,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
    driver = Chrome(options=options)
    driver.set_window_size(1560, 720)

    driver.get(NTTA_URL)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, TOLL_USERNAME_ID)))
    print('writing username.')
    login = driver.find_element(By.ID, TOLL_USERNAME_ID)
    login.clear()
    login.send_keys(NTTA_LOGIN)
    print('writing password.')
    password = driver.find_element(By.NAME, TOLL_PASSWORD_NAME)
    password.clear()
    password.send_keys(NTTA_PASSWORD)
    print('clicking button.')
    sleep(5)
    driver.find_element(By.CSS_SELECTOR, TOLL_LOGIN_BUTTON_SELECTOR).click()
    sleep(5)
    driver.get(NTTA_HISTORY_URL)
    driver.refresh()
    print('downloading csv.')
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, TOLL_CSV_XPATH)))
    driver.find_element(By.XPATH, TOLL_CSV_XPATH).click()
    sleep(10)
    print('quitting from browser.')
    driver.quit()

    #read.py
    with open(TOLL_FILENAME, 'r', encoding='utf-8') as fl:
        print('reading csv file.')
        csv_fl = reader(fl)

        readed_data: list[list] = []
        count = 0
        for row in csv_fl:
            if count != 0:
                readed_data.append(row[2:12])
            count += 1

        for row in readed_data:
            for col in row:
                row[row.index(col)] = col.replace('=Text("', '')\
                    .replace('","mm/dd/yyyy HH:mm:SS")', '').replace('$', '')
            row[0] = dt.strptime(row[0], '%m/%d/%Y %H:%M:%S')

        tolls: list[dict] = []
        for row in readed_data:
            if row[0].strftime('%m.%d.%Y') in [
                (dt.now(texas_tz) - timedelta(days=i)).strftime('%m.%d.%Y') for i in range(4)
            ]:
                tolls.append({
                    'date': row[0],
                    'id': int(row[1]),
                    'location': row[2],
                    'plate': row[4][row[4].rfind(' ') + 1:len(row[4])],
                    'type': row[5],
                    'sum': row[8],
                    'toll_tag_id': row[3]
                })
    remove(TOLL_FILENAME)

    #send.py
    print('writing tolls to firebase.')
    reads = 0
    tasks: list[dict] = to_dict_all(db.collection('Task')
        .where(field=FieldFilter('name_task', '==', TOLL_NAME_TASK))
        .where(filter=FieldFilter('status', '==', True)).get())
    reads += len(tasks)
    exists_tolls_dict: list[dict] = to_dict_all(db.collection('Toll')\
        .where(filter=FieldFilter('date', '>=', dt.now(texas_tz) - timedelta(days=31))).get())
    reads += len(exists_tolls_dict)
    exists_tolls: list[int] = [int(toll['ID']) for toll in exists_tolls_dict]

    for toll in tolls:
        if toll['plate'] == '' or toll['plate'] == '-':
            continue
        if toll['id'] not in exists_tolls:
            car = get_car(db, toll['plate'], 'plate')
            reads += 1
            if car['nickname'] is not None:
                if toll['plate'] != '' or toll['plate'] != '-':
                    contract_name = get_contract(db, car['nickname'], check_active=False)\
                        ['ContractName']
                    reads += 1
                    print(
                        f'write toll {toll["id"]}, nickname: '
                        f'{car["nickname"] if has_key(car, "nickname") else "-"}, date: '
                        f'{toll["date"]}, id: {toll["id"]}, sum: {toll["sum"].replace("-", "")}.')
                    if '--read-only' not in argv:
                        db.collection('Pay_contract').add({
                            'date': toll['date'],
                            'id': toll['id'],
                            'sum': float(toll['sum'].replace('-', '')) * 1.1,
                            'plate': toll['plate'],
                            'name_pay': TOLL_NAME_PAY,
                            'category': TOLL_CATEGORY,
                            'comment': f"Original sum: {float(toll['sum'].replace('-', ''))}. " +
                            TOLL_COMMENT_PAY.replace('{location}', toll['location'])\
                                .replace('{type}', toll['type']),
                            'income': False,
                            'expense': True,
                            'owner': False,
                            'delete': False,
                            'odometer': car['odometer'],
                            'ContractName': contract_name,
                            'nickname': car['nickname'],
                            'user': USER
                        })
                        db.collection('Toll').document(str(toll['id'])).set({
                            'date': toll['date'],
                            'ID': toll['id'],
                            'sum': float(toll['sum'].replace('-', '')),
                            'plate': toll['plate'],
                            'location': toll['location'],
                            'type': toll['type'],
                            'nickname': car['nickname'],
                            'paid': True
                        })
                    else:
                        print('toll not writed because of "--read-only" flag.')
            else:
                if toll['plate'] not in [
                    task['plate'] for task in tasks if (has_key(task, 'plate'))
                ]:
                    print(f'write unknown toll task - plate: {toll["plate"]}, id: {toll["id"]}')
                    db.collection('Task').add({
                        'date': dt.now(texas_tz),
                        'name_task': TOLL_NAME_TASK,
                        'comment': TOLL_COMMENT_TASK.replace('{sum}', str(toll['sum']))\
                            .replace('{id}', str(toll['id'])).replace('{plate}', toll['plate']),
                        'user': USER,
                        'plate': toll['plate'],
                        'status': True,
                        'nickname': '49M-TEST',
                        'id': toll['id']
                    })
        #else:
        #    print(f'skip {toll["id"]}.')

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'toll_update': dt.now(texas_tz)})
        print('set last toll update.')
    else:
        print('toll last update not updated because of "--read-only" flag.')

def check_toll(last_update_data: dict, db, log: bool = False) -> None:
    """check toll last update"""
    if log:
        print('check toll last update.')
    if last_update_data['toll_update'].astimezone(texas_tz) + timedelta(hours=3)\
        <= dt.now(texas_tz):
        print('toll has not been started for a long time: starting...')
        start_toll(db)
    else:
        if log:
            print('toll was started recently. All is ok.')
