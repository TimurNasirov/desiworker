"""
runner.py
=======

Main entry point that coordinates all periodic tasks and listeners in the DESI CARS automation
system.

Functions
------------
• **Launches checking functions**
  - Checks when key services were last updated (via `Last_update_python/last_update`)
  - Triggers `check_*` functions like `check_changeoil`, `check_insurance`, etc.

• **Starts continuous listeners**
  - Launches background listeners that react to Firestore or Firebase updates:
    - Odometer updates
    - Owner uploads
    - Rental changes
    - Toll activity
    - Payment summaries, and more

• **Schedules periodic tasks by time**
  - Runs specific jobs at exact times throughout the day:
    - 11:57 – rentacar block (change oil, payday, insurance, etc.)
    - 11:45 / 23:51 / 06:00 – odometer
    - 23:57 – supadesш
    - 13:02 / 12:00 – payevery and IMEI

• **Provides full start option**
  - You can run `start_all()` to launch all key subsystems manually (used in tests or full boot)

"""
from rentacar.log import Log
from rentacar.mods.timemod import time_is, wait
from rentacar.mods.firemod import init_db, bucket

from rentacar.changeoil import start_changeoil, check_changeoil
from rentacar.insurance import start_insurance, check_insurance
from rentacar.latepayment import start_latepayment, check_latepayment
from rentacar.odometer import start_odometer, check_odometer, odometer_listener
from rentacar.payday import start_payday, check_payday
from rentacar.post import start_post, check_post
from rentacar.registration import start_registration, check_registration
from rentacar.saldo import start_saldo, check_saldo, saldo_listener
from rentacar.supadesi import start_supadesi
from rentacar.payevery import start_payevery, start_payevery2, check_payevery
from rentacar.imei import start_imei
from rentacar.extoll import extoll_listener
from rentacar.owner import owner_listener
from rentacar.lease import lease_listener
from rentacar.rental import rental_listener
from rentacar.statement import statement_listener
from rentacar.card import card_listener
from rentacar.debtreport import debt_listener
from rentacar.incomes import incomes_listener

logdata = Log('runner.py')
print = logdata.print

db = init_db()
bucket = bucket()

def run_checking(run) -> None:
    """Runs all checks and background listeners based on enabled features in `run`."""
    last_update_data = db.collection('Last_update_python').document('last_update').get().to_dict()
    if not last_update_data:
        raise ValueError('last update data is null')

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
    if 'payevery' in run:
        check_payevery(last_update_data, db)
    if 'saldo' in run:
        check_saldo(last_update_data, db)

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
    if 'statement' in run:
        statement_listener(db, bucket)
    if 'card' in run:
        card_listener(db, bucket)
    if 'saldo' in run:
        saldo_listener(db)
    if 'debt' in run:
        debt_listener(db, bucket)
    if 'incomes' in run:
        incomes_listener(db, bucket)

    while True:
        if time_is('11:57'):
            start_rentacar(run)

        elif time_is('11:45') or time_is('23:51') or time_is('06:00'):
            if 'odometer' in run:
                start_odometer(db)

        elif time_is('23:57'):
            if 'supadesi' in run:
                start_supadesi(db)

        elif time_is('13:02'):
            if 'payevery' in run:
                start_payevery(db)

        elif time_is('12:00'):
            if 'payevery' in run:
                start_payevery2(db)
            if 'imei' in run:
                start_imei(db)

        wait()

def start_all(run) -> None:
    """Manually triggers the full startup for the selected modules."""
    if 'odometer' in run:
        start_odometer(db)
    start_rentacar(run)
    if 'supadesi' in run:
        start_supadesi(db)

def start_rentacar(run) -> None:
    """Runs core rentacar modules like oil change, insurance, late payments, etc."""
    if 'changeoil' in run:
        start_changeoil(db)
    if 'payday' in run:
        start_payday(db)
    if 'insurance' in run:
        start_insurance(db)
    if 'registration' in run:
        start_registration(db)
    if 'post' in run:
        start_post(db)
    if 'saldo' in run:
        start_saldo(db)
    if 'latepayment' in run:
        start_latepayment(db)
    if 'payevery' in run:
        start_payevery(db)
        start_payevery2(db)
    if 'imei' in run:
        start_imei(db)

if __name__ == '__main__':
    print('Run main process -> python main.py')
    print('There is not mean to activate this file, because this is doing nothing.')
