'''
POST
When task is postponed and post_time indicated and it`s today, this program change task status to True and post to False (returns to the state
that was before postponement)
If main process don`t launch longer than 24 hours, and after that it starts, this program will start immediately.
After check all tasks, post_last_update will update to current time.

Collection: Task
Group: rentacar
Launch time: 11:57 [rentacar]
Marks: last-update
'''

from sys import path, argv
from os.path import dirname, abspath
from os import get_terminal_size


from rentacar.log import Log
from rentacar.mods.timemod import dt, timedelta, texas_tz, time
from rentacar.mods.firemod import to_dict_all, has_key, client, init_db

logdata = Log('post.py')
print = logdata.print

def start_post(db: client):
    """start post

    Args:
        db (client): database
    """
    print('start post.')
    start_time = time()
    tasks: list[dict] = to_dict_all(db.collection('Task').get())

    for task in tasks.copy():
        if has_key(task, 'post_time') and has_key(task, 'post'):
            if task['post_time'].astimezone(texas_tz) > dt.now(texas_tz) or not task['post']:
                tasks.remove(task)
        else:
            tasks.remove(task)

    for task in tasks:
        update_task(db, task)

    print(f'total post tasks: {len(tasks)}')

    if '--read-only' not in argv:
        db.collection('Last_update_python').document('last_update').update({'post_update': dt.now(texas_tz)})
        print('set last post update.')
    else:
        print('post last update not updated because of "--read-only" flag.')
    print(f'Post work completed. Updated tasks: {len(tasks)}. Time: {round(time() - start_time, 2)} seconds.')

def update_task(db: client, task: dict):
    """Update a task`s status

    Args:
        db (client): database
        task (dict): task data
    """
    print(f'write post - nickname: {task["nickname"]}')
    if '--read-only' not in argv:
        db.collection('Task').document(task['_firebase_document_id']).update({
            'status': True,
            'post': False
        })

    else:
        print('task not updated because of "--read-only" flag.')


def check_post(last_update_data: dict, db: client, log: bool = False):
    """check post last update

    Args:
        last_update_data (dict): last update
        db (client): database
        log (bool, optional): show log. Defaults to False.
    """
    if log:
        print('check post last update.')
    if last_update_data['post_update'].astimezone(texas_tz) + timedelta(hours=24) <= dt.now(texas_tz):
        print('post has not been started for a long time: starting...')
        start_post(db)
    else:
        if log:
            print('post was started recently. All is ok.')
