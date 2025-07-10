"""File that write and save logs in folder logs/"""
from datetime import datetime as dt
from os import listdir
from mods.timemod import texas_tz
from sys import argv

_print = print
dirr = '/container/logs/' if '-d' in argv else 'logs/'
class Log:
    """Class for creating logs"""
    def __init__(self, file) -> None:
        """Initialize the object from a file

        Args:
            file (str): name of file
        """
        self.file = file
        self.date = dt.now(texas_tz).strftime('%d.%m')

    def logfile(self, log) -> None:
        """write a log file to the current date

        Args:
            log (str): log data
        """
        pass
        # if self.date + '.txt' in listdir(dirr):
        #     with open(dirr + self.date + '.txt', 'a', encoding="utf-8") as fl:
        #         fl.write(log + '\n')
        # else:
        #     with open(dirr + self.date + '.txt', 'x', encoding="utf-8"):
        #         pass
        #     self.logfile(log)

    def log_init(self, command) -> None:
        """create log file

        Args:
            command (str): command from that file starts
        """
        pass
        # with open(dirr + self.date + '.txt', 'a', encoding="utf-8") as fl:
        #     fl.write(f'launch at {dt.now(texas_tz).strftime("%d.%m %H:%M")} ({command})\n')

    def print(self, log) -> None:
        """Print a log message

        Args:
            log (str): log data
        """
        self.date = dt.now(texas_tz).strftime('%d.%m')
        logdata = f'[{dt.now(texas_tz).strftime("%d.%m %H:%M:%S")}] {self.file}: {log}'

        self.logfile(logdata)
        _print(logdata)
