"""File that write and save logs in folder logs/"""
from datetime import datetime as dt
from os import listdir

_print = print
class Log:
    """Class for creating logs"""
    def __init__(self, file):
        """Initialize the object from a file

        Args:
            file (str): name of file
        """
        self.file = file
        self.date = dt.now().strftime('%d.%m')

    def logfile(self, log):
        """write a log file to the current date

        Args:
            log (str): log data
        """
        if self.date + '.txt' in listdir('logs/'):
            with open('logs/' + self.date + '.txt', 'a', encoding="utf-8") as fl:
                fl.write(log + '\n')
        else:
            with open('logs/' + self.date + '.txt', 'x', encoding="utf-8"):
                pass
            self.logfile(log)

    def log_init(self, command):
        """create log file

        Args:
            command (str): command from that file starts
        """
        with open('logs/' + self.date + '.txt', 'a', encoding="utf-8") as fl:
            fl.write(f'launch at {dt.now().strftime("%d.%m %H:%M")} ({command})\n')

    def print(self, log):
        """Print a log message

        Args:
            log (str): log data
        """
        self.date = dt.now().strftime('%d.%m')
        logdata = f'[{dt.now().strftime("%d.%m %H:%M:%S")}] {self.file}: {log}'

        self.logfile(logdata)
        _print(logdata)
