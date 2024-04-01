import datetime
import sys
from typing import List

from models.Task import Task
from models.Project import Project
from utils.MemTime import query_time_entries, query_project, query_tasks
from utils.LiquidPlanner import fetch_my_account, fetch_member, fetch_tasks_by_ids, post_timesheet_entry
from utils.Util import ask_question, get_epoch_from_datetime


# Value cannot be None, leave empty string if not used.
SHARED_TIME_PROJECT_NAME = 'Shared Time'

SECONDS_IN_DAY = 60 * 60 * 24

def get_date_input() -> datetime.datetime:
    while True:
        date_str = input('Enter date or press enter for today [dd/mm/yyyy]: ')
        if date_str == '':
            date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            try:
                date = datetime.datetime.strptime(date_str, '%d/%m/%Y')
            except ValueError:
                print('Invalid date format. Please try again.')
                continue
        
        while True:
            confirm = input(f'Confirm date "{date.strftime('%d/%m/%Y')}" [y/n]: ').lower()
            if confirm == 'y':
                return date
            elif confirm == 'n':
                break

def get_duplicate_task_references(tasks: List[Task]) -> List[str]:
    duplicate_lp_references: List[str] = []
    lp_task_ids = [task.liquid_planner_task_id for task in tasks]
    for i in range(len(tasks)):
        task = tasks[i]
        if task.liquid_planner_task_id is not None and lp_task_ids.index(task.liquid_planner_task_id) != i:
            info_string = f'{task.liquid_planner_url} ({task.label}, {tasks[i].label})'
            duplicate_lp_references.append(info_string)
    return duplicate_lp_references

def print_timesheet_summary(tasks_to_timesheet: List[Task], shared_time_project: Project, shared_time_multiplier: int):
    total_time = round(sum([task.get_logged_time_hrs() for task in (tasks_to_timesheet + shared_time_project.tasks)]), 2)
    print(f'\nTotal Time: {total_time} hrs')
    print('Tasks:')
    for task in tasks_to_timesheet:
        print(f'\t{task.get_print_summary(False)}')
        
    if shared_time_project is not None:
        print()
        for task in shared_time_project.tasks:
            print(f'\t{task.get_print_summary(True)}')
        print(f'\nShared time multiplier is: {round(shared_time_multiplier, 2)}')
    print()

def main():
    # Get date to log timesheet
    date = get_date_input()
    start_epoch = get_epoch_from_datetime(date)
    end_epoch = start_epoch + SECONDS_IN_DAY

    # Fetch timesheet entries from database
    timesheet_entries = query_time_entries(start_epoch, end_epoch)
    entity_ids = list(set(entry.entity_id for entry in timesheet_entries))

    # Fetch shared time project
    if len(SHARED_TIME_PROJECT_NAME) == 0:
        shared_time_project = None
    else:
        projects = query_project(SHARED_TIME_PROJECT_NAME)
        if len(projects) > 0:
            shared_time_project = projects[0]
        else:
            print(f'Could not find a shared time project for {SHARED_TIME_PROJECT_NAME}')
            sys.exit(1)

    # Fetch tasks from database
    tasks = query_tasks(entity_ids)
    for task in tasks:
        if shared_time_project != None and task.parent_id == shared_time_project.id:
            shared_time_project.add_task(task)
            continue

        try:
            success = task.set_id_from_url()
            if success:
                continue
        except:
            pass

        confirmed = ask_question(f'ERROR: Ensure LiquidPlanner URL in Memtime task description is valid for "{task.label}"\nDo you want to skip timesheet for this task?')
        if not confirmed:
            print('Cancelled')
            sys.exit(1)

    # Check if two MemTime tasks reference the same LP task
    duplicate_lp_tasks = get_duplicate_task_references(tasks)
    if len(duplicate_lp_tasks) > 0:
        print()
        for info_string in duplicate_lp_tasks:
            print(info_string)

        print(f'\nThe above LiquidPlanner tasks were each referenced by more than one MemTime task.')
        print(f'Please resolve this before continuing')
        sys.exit(1)

    # Map MemTime timesheet entries to MemTime tasks
    queries_task_ids = [task.id for task in tasks]
    for entry in timesheet_entries:
        try:
            task_index = queries_task_ids.index(entry.entity_id)
            tasks[task_index].add_entry(entry)
        except ValueError:
            print(f'WARNING: Failed to query a task for timesheet entry "{entry}"')
    
    # Get default activity information
    user_account = fetch_my_account()
    member_id = user_account['id']
    member = fetch_member(member_id)
    default_activity_id = member['default_activity_id']

    # Find non-shared time tasks
    tasks_to_timesheet = [task for task in tasks if task.id not in shared_time_project.get_task_ids()]

    # Fetch, validate and map LiquidPlanner tasks
    liquid_planner_task_ids = [task.liquid_planner_task_id for task in tasks_to_timesheet]
    tasks_json = fetch_tasks_by_ids(liquid_planner_task_ids)

    lp_task_ids = [task['id'] for task in tasks_json]
    for task in tasks_to_timesheet:
        try:
            lp_task_index = lp_task_ids.index(task.liquid_planner_task_id)
        except ValueError:
            print(f'ERROR: Could not find LiquidPlanner task for "{task.label}"')
            sys.exit(1)
        
        task.set_liquid_planner_task(member_id, default_activity_id, tasks_json[lp_task_index])
    
    # Calculate and set shared time multiplier
    shared_time_multiplier = 1.0
    if shared_time_project is not None:
        total_time = sum([task.get_logged_time_hrs() for task in tasks])
        total_shared_project_time = shared_time_project.get_total_task_time()
        shared_time_multiplier = total_time / (total_time - total_shared_project_time)
    
    # Confirm timesheet
    print_timesheet_summary(tasks_to_timesheet, shared_time_project, shared_time_multiplier)

    confirmed = ask_question('Confirm you want to submit your timesheet as shown above?')
    if not confirmed:
        print('Cancelled')
        sys.exit(1)
    
    # Save to LiquidPlanner
    post_dt = date.replace(hour=17)
    now = datetime.datetime.now()
    if now < post_dt:
        post_dt = now

    for task in tasks_to_timesheet:
        logged_time_hrs = round(task.get_logged_time_hrs() * shared_time_multiplier, 2)
        body = {
            'work': logged_time_hrs,
            'activity_id': task.liquid_planner_activity_id,
            'low': max(task.liquid_planner_remaining_low - logged_time_hrs, 0),
            'high': max(task.liquid_planner_remaining_high - logged_time_hrs, 0),
            'work_performed_on': post_dt.isoformat()
        }

        try:
            post_timesheet_entry(task.liquid_planner_task_id, body)
        except Exception as ex:
            print(f'ERROR: Failed to upload timesheet entry for "{task.label}"')
            print(ex)

main()
