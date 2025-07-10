from traceback import format_exception
from requests import get
from rentacar.config import TELEGRAM_LINK
from sys import argv

try:
    from log import Log
    from toll import start_toll
    from runner import db, run_checking

    logdata = Log('main.py')
    print = logdata.print
    logdata.logfile('\n')

    if '--read-only' in argv:
        print('--read-only: no sms sending, no task and pay creating, no last update updating.')
    if '-t' in argv:
        print('-t: immediately activate. Process will stop after all subprocesses finished.')
    if '--no-tg' in argv:
        print('--no-tg: no telegram notifications sending on errors')

    if '-t' in argv:
        start_toll(db)
    else:
        print('start main process.')
        run_checking()

except Exception as e:
    exc_data = format_exception(e)[-2].split('\n')[0]
    line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
    module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
    print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}).')
    if '--no-tg' not in argv:
        get(f'{TELEGRAM_LINK}DESI WORKER: raised error in module {module} ({e.__class__.__name__})')

except KeyboardInterrupt:
    print('main process stopped.')