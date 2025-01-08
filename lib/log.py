from datetime import datetime as dt

_print = print
class Log:
    def __init__(self, file):
        self.file = file

    def print(self, log):
        _print(f'[{dt.now().strftime('%d.%m %H:%M:%S')}] {self.file}: {log}')