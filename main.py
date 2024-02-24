import datetime
import sqlite3
import tzlocal
import json
import sys
from typing import List

from models.TimesheetEntry import TimesheetEntry
from models.Task import Task
from utils.LiquidPlanner import fetch_my_account, fetch_member, fetch_tasks_by_ids, post_timesheet_entry


DATABASE_PATH = 'C:\\Users\\ollie\\AppData\\Local\\memtime\\user\\62d87704d32b2e0009546557\\data\\tb-private-local-projects\\connected-app.tb-private-local-projects.db'
SECONDS_IN_DAY = 60 * 60 * 24

ENTITY_TASK_TYPE = 'task'

def get_date_input() -> datetime.datetime:
    while True:
        try:
            date_str = '24/02/2024'  # TODO: input('Enter date (dd/mm/yyyy): ')
            date = datetime.datetime.strptime(date_str, '%d/%m/%Y')
            return date
        except ValueError:
            print('Invalid date format. Please try again.')

def get_epoch_from_datetime(dt: datetime.datetime) -> int:
    epoch_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
    timezone_offset_secs = -int(dt.astimezone(tzlocal.get_localzone()).utcoffset().total_seconds())
    return (dt - epoch_time).total_seconds() + timezone_offset_secs

def query_time_entries(database_path: str, start_epoch: int, end_epoch: int) -> List[TimesheetEntry]:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    query = '''
        SELECT *
        FROM timeEntry
        WHERE start >= ? AND start < ? AND end >= ? AND end < ?
    '''

    res = cursor.execute(query, (start_epoch, end_epoch, start_epoch, end_epoch))

    time_entries: List[TimesheetEntry] = []
    for entry in res:
        _, _, start_epoch, end_epoch, body, *_ = entry
        entity = json.loads(body)['entity']
        entry = TimesheetEntry(int(entity['value']), entity['entityType'], entity['label'], int(start_epoch), int(end_epoch))
        time_entries.append(entry)

    conn.close()
    return time_entries

def query_tasks(database_path: str, entity_ids: List[int]) -> List[Task]:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    query = f'''
        SELECT *
        FROM entity
        WHERE id in ({','.join(['?'] * len(entity_ids))}) AND type = ?
    '''

    res = cursor.execute(query, entity_ids + [ENTITY_TASK_TYPE])

    tasks: List[Task] = []
    for entity in res:
        id, _, label, liquid_planner_url, *_ = entity
        task = Task(id, label, liquid_planner_url)
        tasks.append(task)
    
    return tasks

def print_timesheet_summary(tasks: List[Task]):
    total_time = sum([task.get_logged_time_hrs() for task in tasks])
    print(f'\nTotal Time: {total_time} hrs')
    print('Tasks:')
    for task in tasks:
        print(f'\t{task.get_print_summary()}')
    print()

def main():
    # Get date to log timesheet
    date = get_date_input()
    start_epoch = get_epoch_from_datetime(date)
    end_epoch = start_epoch + SECONDS_IN_DAY

    # Fetch timesheet entries from database
    timesheet_entries = query_time_entries(DATABASE_PATH, start_epoch, end_epoch)
    entity_ids = list(set(entry.entity_id for entry in timesheet_entries))

    # Fetch tasks from database and map timesheet entries
    tasks = query_tasks(DATABASE_PATH, entity_ids)
    queries_task_ids = [task.id for task in tasks]
    for entry in timesheet_entries:
        try:
            task_index = queries_task_ids.index(entry.entity_id)
            tasks[task_index].add_entry(entry)
        except ValueError:
            print(f'ERROR: Failed to query a task for timesheet entry "{entry}"')
            sys.exit(1)
    
    # Get default activity information
    user_account = fetch_my_account()
    member_id = user_account['id']
    member = fetch_member(member_id)
    default_activity_id = member['default_activity_id']

    # Fetch, validate and map LiquidPlanner tasks
    liquid_planner_task_ids = [task.liquid_planner_task_id for task in tasks]
    tasks_json = fetch_tasks_by_ids(liquid_planner_task_ids)
    print(json.dumps(tasks_json))

    lp_task_ids = [task['id'] for task in tasks_json]
    for task in tasks:
        try:
            lp_task_index = lp_task_ids.index(task.liquid_planner_task_id)
        except ValueError:
            print(f'ERROR: Could not find LiquidPlanner task for "{task.label}"')
            sys.exit(1)
        
        task.set_liquid_planner_task(member_id, default_activity_id, tasks_json[lp_task_index])
    
    # Confirm timesheet
    print_timesheet_summary(tasks)

    confirmed = False
    while not confirmed:
        res = input('Confirm you want to submit your timesheet as shown above? [y/n]').lower()
        if res == 'y':
            confirmed = True
        elif res == 'n':
            print('Cancelled')
            sys.exit(1)
    
    # Save to LiquidPlanner
    post_dt = date.replace(hour=17)
    now = datetime.datetime.now()
    if now < post_dt:
        post_dt = now

    for task in tasks:
        body = task.get_post_task_body()
        body['work_performed_on'] = post_dt.isoformat()
        print(body)

        try:
            post_timesheet_entry(task.liquid_planner_task_id, body)
        except Exception as ex:
            print(f'ERROR: Failed to upload timesheet entry for "{task.label}"')
            print(ex)

main()
