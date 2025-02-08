from sys import path, argv
from os.path import dirname, abspath
from csv import reader
from os import get_terminal_size
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from lib.log import Log
from lib.mods.firemod import client, to_dict_all, get_car, has_key
from lib.mods.timemod import sleep, dt, timedelta
from config import NTTA_URL, NTTA_LOGIN, NTTA_PASSWORD, NTTA_HISTORY_URL
from lib.str_config import TOLL_USERNAME_ID, TOLL_PASSWORD_NAME, TOLL_LOGIN_BUTTON_SELECTOR, TOLL_CSV_XPATH, TOLL_FILENAME
logdata = Log('toll.py')
print = logdata.print

def start_toll(db: client):
    print('start toll.')
    #download.py
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
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
    with open(TOLL_FILENAME, 'r') as fl:
        print('reading csv file.')
        csv_fl: list = reader(fl)
        
        readed_data: list[list] = []
        for row in csv_fl:
            if csv_fl[0] != row:
                readed_data.append(row[2:12])
        
        for row in readed_data:
            for col in row:
                row[row.index(col)] = col.replace('=Text("', '').replace('","mm/dd/yyyy HH:mm:SS")', '').replace('$', '')
            row[0] = dt.strptime(row[0], '%m/%d/%Y %H:%M:%S')
        
        tolls: list[list] = []
        for row in readed_data:
            if row[0].strftime('%m.%d.%Y') in [(dt.now() - timedelta(days=i)).strftime('%m.%d.%Y') for i in range(4)]:
                tolls.append({'date': row[0], 'ID': int(row[1]), 'location': i[2], 'toll_tag_id': i[3], 'plate': i[4][i[4].rfind(' ') + 1:len(i[4])], 'type': i[5], 'balance_before': i[7], 'transaction': i[8], 'balance_after': i[9]})

    #send.py
    print('writing tolls to firebase.')
    exists_tolls_dict: list[dict] = to_dict_all(db.collection('Toll').get())
    exists_tolls: list[int] = []
    for toll in exists_tolls_dict:
        exists_tolls.append(int(toll['ID']))
    
    for toll in tolls:
        if toll['id'] not in exists_tolls:
            car = get_car(db, toll['plate'], 'plate')
            if car['nickname'] != None:
                toll['nickname'] = car['nickname']
            print(f'write toll {toll["id"]}, nickname: {toll["nickname"] if has_key(toll, 'nickname') else '-'}.')
            db.collection('Toll').document(str(toll['id'])).set(toll)
        else:
            print(f'skip {toll["id"]}.')

        
def check_toll(db):
    pass