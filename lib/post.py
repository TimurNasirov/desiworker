from .log import Log
logdata = Log('post.py')
print = logdata.print

def start_post(db):
    print('start post.')

def check_post(db):
    pass