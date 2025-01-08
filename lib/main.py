from .log import Log
from .mods.timemod import time_is, wait
from time import sleep
from firebase_admin.credentials import Certificate
from firebase_admin.firestore import client
from firebase_admin import initialize_app

from .changeoil import *; from .excel import *; from .insurance import *; from .latepayment import *; from .odometer import *
from .payday import *; from .post import *; from .registartion import *; from .saldo import *; from .toll import *;  from .word import *
from .supadesi import *

logdata = Log('main.py')
print = logdata.print
cred = Certificate('key.json')
initialize_app(cred)
db = client()

def run_checking(run):
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