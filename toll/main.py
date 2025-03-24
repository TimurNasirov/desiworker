from traceback import format_exception
from requests import get
from config import TELEGRAM_LINK

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
        print('--no-tg: no telegram notifications sneding on errors')

    if '-t' in argv:
        start_toll(db)
    else:
        print('start main process.')
        run_checking()

except Exception as e:
    exc_data = format_exception(e)[-2].split('\n')[0]
    line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
    module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
    if '--no-tg' not in argv:
        print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}).')

except KeyboardInterrupt:
    print('main process stopped.')