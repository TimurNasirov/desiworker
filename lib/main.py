"""
Main program thats launch every other programs (without watcher.py)
Launch times:
rentacar: 11:57
odometer: 11:50, 23:51, 6:00
supadesi: 23:57
toll: 23:45, 12:10
"""

from sys import path
from os.path import dirname, abspath
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from time import sleep
from lib.log import Log
from lib.mods.timemod import time_is, wait
from lib.mods.firemod import init_db, bucket, client

from lib.changeoil import start_changeoil, check_changeoil
from lib.insurance import start_insurance, check_insurance
from lib.latepayment import start_latepayment, check_latepayment
from lib.odometer import start_odometer, check_odometer, odometer_listener
from lib.payday import start_payday, check_payday
from lib.post import start_post, check_post
from lib.registration import start_registration, check_registration
from lib.saldo import start_saldo, check_saldo
from lib.toll import start_toll, check_toll
from lib.supadesi import start_supadesi

from lib.extoll import extoll_listener
from lib.owner import owner_listener
from lib.lease import lease_listener
from lib.rental import rental_listener

logdata = Log('main.py')
print = logdata.print

db: client = init_db()
bucket = bucket()

def run_checking(run):
    """Run all subprocesses in a run

    Args:
        run (list): objects that should run
    """
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
        check_odometer(last_update_data, db)
    if 'payday' in run:
        check_payday(last_update_data, db)
    if 'post' in run:
        check_post(last_update_data, db)
    if 'registration' in run:
        check_registration(last_update_data, db)

    print('initialize listeners.')
    if 'odometer' in run:
        odometer_listener(db)
    if 'owner' in run:
        owner_listener(db, bucket)
    if 'lease' in run:
        lease_listener(db, bucket)
    if 'rental' in run:
        rental_listener(db, bucket)
    if 'extoll' in run:
        extoll_listener(db, bucket)

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
    """Start all of the things in the run

    Args:
        run (list): objects that should run
    """
    sleep(1)
    if 'odometer' in run:
        start_odometer(db)
    start_rentacar(run)
    if 'toll' in run:
        start_toll(db)
    if 'supadesi' in run:
        start_supadesi(db)

def start_rentacar(run):
    """Starts the various boilerplate functions in the run

    Args:
        run (list): objects that should run
    """
    if 'changeoil' in run:
        start_changeoil(db)
    if 'payday' in run:
        start_payday(db)
    if 'insurance' in run:
        start_insurance(db)
    if 'registartion' in run:
        start_registration(db)
    if 'post' in run:
        start_post(db)
    if 'saldo' in run:
        start_saldo(db)
    if 'latepayment' in run:
        start_latepayment(db)

if __name__ == '__main__':
    print('Run main process -> python watcher.py')
    print('There is not mean to activate this file, because this is doing nothing.')
