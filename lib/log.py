from datetime import datetime as dt
from os import listdir

_print = print
class Log:
    def __init__(self, file):
        self.file = file
        self.date = dt.now().strftime('%d.%m')
    
    def logfile(self, log):
        if self.date + '.txt' in listdir('logs/'):
            with open('logs/' + self.date + '.txt', 'a') as fl:
                fl.write(log + '\n')
        else:
            fl = open('logs/' + self.date + '.txt', 'x')
            fl.close()
            self.logfile(log)
    
    def log_init(self, command):
        fl = open('logs/' + self.date + '.txt', 'a')
        fl.write(f'launch at {dt.now().strftime("%d.%m %H:%M")} ({command})\n')
        fl.close()

    def print(self, log):
        self.date = dt.now().strftime('%d.%m')
        logdata = f'[{dt.now().strftime('%d.%m %H:%M:%S')}] {self.file}: {log}'
        
        self.logfile(logdata)
        _print(logdata)