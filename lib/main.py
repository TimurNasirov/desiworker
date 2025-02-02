from lib.log import Log
from lib.mods.timemod import time_is, wait
from lib.mods.firemod import init_db, bucket
from time import sleep

from .changeoil import *; from .excel import *; from .insurance import *; from .latepayment import *; from .odometer import *
from .payday import *; from .post import *; from .registration import *; from .saldo import *; from .toll import *;
from .word import *; from .supadesi import *

logdata = Log('main.py')
print = logdata.print

db: client = init_db()
bucket = bucket()

def run_checking(run):
    last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
    
    print('checking subprocesses on last update.')
    if 'changeoil' in run:
        check_changeoil(last_update_data, db)
    if 'insurance' in run:
        check_insurance(last_update_data, db)
    if 'latepayment' in run:
        check_latepayment(last_update_data, db)
    if 'payday' in run:
        check_payday(last_update_data, db)
    if 'odometer' in run:
        #check_odometer(last_update_data, db)
        pass
    
    print('initialize listeners.')
    if 'odometer' in run:
        odometer_listener(db)
    if 'exword' in run:
        excel_listener(db, bucket)
        word_listener(db, bucket)
    
    while True:
        if time_is('11:57'):
            start_rentacar(run)
        
        elif time_is('11:50') or time_is('23:51') or time_is('06:00'):
            if 'odometer' in run:
                start_odometer(db)
        
        elif time_is('23:57'):
            if 'supadesi' in run:
                start_supadesi(db)
        
        elif time_is('23:45') or time_is('12:10'):
            if 'toll' in run:
                start_toll(db)
            
        wait()

def start_all(run):
    sleep(1)
    if 'odometer' in run:
        start_odometer(db)
    start_rentacar(run)
    if 'toll' in run:
        start_toll(db)
    if 'supadesi' in run:
        start_supadesi(db)

def start_rentacar(run):
    if 'changeoil' in run:
        start_changeoil(db)
    if 'payday' in run:
        start_payday(db)
    if 'insurance' in run:
        start_insurance(db)
    if 'registartion' in run:
        start_registartion(db)
    if 'post' in run:
        start_post(db)
    if 'saldo' in run:
        start_saldo(db)
    if 'latepayment' in run:
        start_latepayment(db)

if __name__ == '__main__':
    print('Run main process -> python watcher.py')
    print('There is not mean to activate this file, because this is doing nothing.')