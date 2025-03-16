from traceback import format_exception
try:
    from mods.timemod import time_is, wait
    from mods.firemod import init_db, client
    from toll import start_toll, check_toll
    from log import Log
    from sys import argv

    logdata = Log('runner.py')
    print = logdata.print
    db: client = init_db()

    last_update_data: dict = db.collection('Last_update_python').document('last_update').get().to_dict()
    print('check toll last update.')
    check_toll(last_update_data, db)

    if '-t' in argv:
        print('start immediately activate toll.')
        start_toll(db)
        quit()
    else:
        while True:
            if time_is('23:45') or time_is('12:10'):
                start_toll(db)
            wait()
except Exception as e:
    exc_data = format_exception(e)[-2].split('\n')[0]
    line = exc_data[exc_data.find('line ') + 5:exc_data.rfind(',')]
    module = exc_data[exc_data.find('"') + 1:exc_data.rfind('"')]
    print(f'ERROR in module {module}, line {line}: {e.__class__.__name__} ({e}).')

except KeyboardInterrupt:
    print('main process stopped.')