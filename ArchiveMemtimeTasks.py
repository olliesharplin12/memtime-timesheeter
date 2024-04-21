import datetime
from typing import List

from models.Task import Task
from utils.MemTime import query_tasks, set_task_is_active
from utils.LiquidPlanner import fetch_tasks_by_ids, fetch_my_account
from utils.Util import ask_question


EXPIRED_TASK_AGE_DAYS = 7

def archive_memtime_tasks():
    # Read all Tasks in MemTime and filter active tasks
    active_tasks = [task for task in query_tasks() if task.is_active]

    # Filter LiquidPlanner IDs
    liquid_planner_ids = list(set([task.liquid_planner_id for task in active_tasks if task.liquid_planner_id is not None]))

    # Get All LiquidPlanner Tasks
    liquid_planner_tasks = fetch_tasks_by_ids(liquid_planner_ids)

    # Get current member ID and expiry date string (UTC)
    user_account = fetch_my_account()
    member_id = user_account['id']

    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    expiry_datetime = current_datetime - datetime.timedelta(days=EXPIRED_TASK_AGE_DAYS)

    # Identify tasks to archive
    tasks_to_archive: List[Task] = []
    for lp_task in liquid_planner_tasks:
        memtime_tasks = [task for task in active_tasks if task.liquid_planner_id == lp_task['id']]
        for task in memtime_tasks:
            task.set_liquid_planner_task(lp_task, member_id)
            if task.is_expired(expiry_datetime):
                tasks_to_archive.append(task)
    
    if len(tasks_to_archive) > 0:
        # Confirm with user before archiving tasks
        print(f'\nThe tasks below have had your assignment marked done for longer than {EXPIRED_TASK_AGE_DAYS} days:')
        for memtime_task in tasks_to_archive:
            print(f'\t{memtime_task.get_print_summary(False)}')
        
        print('\nIf there are any tasks above which you do not want to archive, toggle their done flag on LiquidPlanner before running this script again.')
        archive_tasks = ask_question('Do you want to archive the above tasks?')
        if archive_tasks:
            for task in tasks_to_archive:
                set_task_is_active(task.id, False)
    else:
        print('No tasks to archive')


if __name__ == '__main__':
    archive_memtime_tasks()
