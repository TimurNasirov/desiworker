from traceback import format_exception
from requests import get
from config import TELEGRAM_LINK
from sys import argv
try:
    from log import Log
    from os import get_terminal_size
    from runner import start_all, start_rentacar, start_odometer, start_all, start_supadesi, run_checking, db

    logdata = Log('main.py')
    print = logdata.print
    logdata.logfile('\n')

    command = ''
    for i in argv:
        command += i + ' '
    logdata.log_init(command)

    if '--read-only' in argv:
        print('--read-only: no sms sending, no task and pay creating, no last update updating.')
    elif '--no-sms' in argv:
        print('--no-sms: no sms sending, no inboxSMS changing.')
    if '-t' in argv:
        print('-t: immediately activate. Process will stop after all subprocesses finished.')
    if '--no-tg' in argv:
        print('--no-tg: no telegram notifications sending on errors')

    if '--no-rentacar' in argv:
        run = ['toll', 'supadesi', 'extoll', 'rental', 'lease', 'owner', 'statement', 'card', 'incomes', 'debt']
    else:
        run = ['changeoil', 'insurance', 'latepayment', 'odometer', 'payday', 'post', 'registration', 'saldo', 'supadesi', 'rental', 'lease',\
            'extoll', 'owner', 'payevery', 'imei', 'statement', 'card', 'debt', 'incomes']

    if '--rentacar-only' in argv:
        run = ['changeoil', 'insurance', 'registration', 'latepayment', 'odometer', 'payday', 'post', 'saldo']
    if '--supadesi-only' in argv:
        run = ['supadesi']
    if '--exword-only' in argv:
        run = ['rental', 'lease', 'owner', 'extoll', 'statement', 'card', 'debt', 'incomes']
    if '--payevery-only' in argv:
        run = ['payevery']
    if '--saldo-only' in argv:
        run = ['saldo']
    if '--registration-only' in argv:
        run = ['registration']
    if '--post-only' in argv:
        run = ['post']
    if '--payday-only' in argv:
        run = ['payday']
    if '--odometer-only' in argv:
        run = ['odometer']
    if '--latepayment-only' in argv:
        run = ['latepayment']
    if '--insurance-only' in argv:
        run = ['insurance']
    if '--changeoil-only' in argv:
        run = ['changeoil']
    if '--rental-only' in argv:
        run = ['rental']
    if '--lease-only' in argv:
        run = ['lease']
    if '--owner-only' in argv:
        run = ['owner']
    if '--extoll-only' in argv:
        run = ['extoll']
    if '--imei-only' in argv:
        run = ['imei']
    if '--statement-only' in argv:
        run = ['statement']
    if '--card-only' in argv:
        run = ['card']
    if '--debt-only' in argv:
        run = ['debt']
    if '--incomes-only' in argv:
        run = ['incomes']

    if '--no-changeoil' in argv:
        run.remove('changeoil')
    if '--no-insurance' in argv:
        run.remove('insurance')
    if '--no-latepayment' in argv:
        run.remove('latepayment')
    if '--no-odometer' in argv:
        run.remove('odometer')
    if '--no-payday' in argv:
        run.remove('payday')
    if '--no-post' in argv:
        run.remove('post')
    if '--no-registration' in argv:
        run.remove('registration')
    if '--no-saldo' in argv:
        run.remove('saldo')
    if '--no-owner' in argv:
        run.remove('owner')
    if '--no-supadesi' in argv:
        run.remove('supadesi')
    if '--no-owner' in argv:
        run.remove('owner')
    if '--no-rental' in argv:
        run.remove('rental')
    if '--no-lease' in argv:
        run.remove('lease')
    if '--no-extoll' in argv:
        run.remove('extoll')
    if '--no-imei' in argv:
        run.remove('imei')
    if '--no-statement' in argv:
        run.remove('statement')
    if '--no-card' in argv:
        run.remove('card')
    if '--no-debt' in argv:
        run.remove('debt')
    if '--no-incomes' in argv:
        run.remove('incomes')

    if '-t' in argv:
        print('start main process (immediately activate).')
        if len(argv) > argv.index('-t') + 1:
            if argv[argv.index('-t') + 1] == 'rentacar':
                start_rentacar(run)
            elif argv[argv.index('-t') + 1] == 'odometer':
                start_odometer(db)
            elif argv[argv.index('-t') + 1] == 'all':
                start_all(run)
            elif argv[argv.index('-t') + 1] == 'supadesi':
                start_supadesi(db)
            else:
                print(f'ERROR unknown module "{argv[argv.index("-t") + 1]}". See watcher instructions (-h flag).')
        else:
            start_all(run)
        print('main process stopped successfully.')
    elif '-h' in argv:
        size = get_terminal_size().columns
        print(f'{"=" * ((size - 43) // 2)} DESIWORKER {"=" * ((size - 43) // 2)}')
        print(f'{" " * ((size - 50) // 2)} WATCHER INSRUCTIONS {" " * ((size - 50) // 2)}')
        print('')
        print('-> for start main process, run watcher.py')
        print('-t [process]: immediately activate main process (without checking time).')
        print(' - process (str) (optional): name of process that will run.')
        print('   - Available values: all, rentacar, exword, supadesi, odometer.')
        print('   - Default: all')
        print('--[subprocess]-only: run only this subprocess.')
        print(' - Available values: changeoil, owner, rental, lease, extoll, insurance, latepayment, odometer, payday, post, registration, sald\
o, supadesi, toll.')
        print(' - If you choose rentacar, these process will run: changeoil, insurance, latepayment, odometer, payday, post, registration, sald\
o.')
        print('--no-[subprocess]: choose which subprocesses wont work.')
        print(' - Available values: changeoil, owner, rental, lease, extoll, insurance, latepayment, odometer, payday, post, registration, sald\
o, supadesi, toll.')
        print(' - If you choose rentacar, these process wont run: changeoil, insurance, latepayment, odometer, payday, post, registration, sald\
o.')
        print('')
        print('default flags:')
        print(' - -h: show help')
        print(' - --no-sms: diasble SMS send (add inbox, send sms API)')
        print(' - --read-only: give access only on data reading (there is no task creating, last update updating, sms sending)')
    else:
        print('start main process.')
        run_checking(run)

except Exception as e:
    exc_data = format_exception(e)[-2].split('\n')[0]
    line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
    module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
    print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}).')
    if '--no-tg' not in argv:
        get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')

except KeyboardInterrupt:
    print('main process stopped.')