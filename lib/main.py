from lib.log import Log
from lib.mods.timemod import time_is, wait
from lib.mods.firemod import init_db
from time import sleep

from .changeoil import *; from .excel import *; from .insurance import *; from .latepayment import *; from .odometer import *
from .payday import *; from .post import *; from .registartion import *; from .saldo import *; from .toll import *;
from .word import *; from .supadesi import *

logdata = Log('main.py')
print = logdata.print

db: client = init_db()

def run_checking(run):
    last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
    
    print('checking subprocesses on last update.')
    if 'changeoil' in run:
        check_changeoil(last_update_data)
    if 'insurance' in run:
        check_insurance(last_update_data)
    
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