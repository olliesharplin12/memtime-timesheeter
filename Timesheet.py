import datetime
import sys
from typing import List

from models.Task import Task
from models.Project import Project
from utils.MemTime import query_time_entries, query_projects, query_tasks
from utils.LiquidPlanner import fetch_my_account, fetch_member, fetch_tasks_by_ids, post_timesheet_entry
from utils.Util import ask_question, get_epoch_from_datetime


# Value cannot be None, leave empty string if not used.
SHARED_TIME_PROJECT_NAME = 'Shared Time'
LOW_REMAINING_TIME_WARNING_HRS = 0.5

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
            confirm = input(f'Confirm date "{date.strftime("%d/%m/%Y")}" [y/n]: ').lower()
            if confirm == 'y':
                return date
            elif confirm == 'n':
                break

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
        projects = query_projects(SHARED_TIME_PROJECT_NAME)
        if len(projects) > 0:
            shared_time_project = projects[0]
        else:
            print(f'Could not find a shared time project for {SHARED_TIME_PROJECT_NAME}')
            sys.exit(1)

    # Fetch tasks from database and validate all time entries can be mapped
    tasks = query_tasks(entity_ids)
    memtime_task_ids = [task.id for task in tasks]
    for entry in timesheet_entries:
        try:
            task_index = memtime_task_ids.index(entry.entity_id)
            tasks[task_index].add_entry(entry)
        except ValueError:
            print(f'ERROR: Failed to query a MemTime task for timesheet entry "{entry}"')
            sys.exit(1)
    
    # Create task lists based on if they are shared time tasks and they have valid LP IDs
    tasks_to_timesheet: List[Task] = []
    invalid_tasks: List[Task] = []

    for task in tasks:
        if shared_time_project != None and task.parent_id == shared_time_project.id:
            shared_time_project.add_task(task)
        elif task.liquid_planner_id == None:
            invalid_tasks.append(task)
        else:
            tasks_to_timesheet.append(task)
    
    # Confirm user wants to proceed with tasks with no LP URL
    invalid_task_ids = [task.id for task in invalid_tasks]
    shared_time_total_tasks: List[Task] = tasks

    if len(invalid_tasks) > 0:
        print('The tasks below do not have a valid LiquidPlanner ID associated with them:')
        for task in invalid_tasks:
            print(f'\t{task.label}')

        print()
        confirmed = ask_question(f'Do you want to skip timesheeting the above task(s)?')
        if not confirmed:
            print('Cancelled')
            sys.exit(1)
        
        shared_time_on_remaining_tasks = ask_question(f'Do you want to split shared time across the remaining tasks, or will you timesheet the above tasks manually?', 'spl', 'man')
        if shared_time_on_remaining_tasks:
            shared_time_total_tasks: List[Task] = [task for task in tasks if task.id not in invalid_task_ids]
    
    # Get default activity information
    user_account: dict = fetch_my_account()
    member_id: int = user_account['id']
    member: dict = fetch_member(member_id)
    default_activity_id: int = member['default_activity_id']

    # Fetch, validate and map LiquidPlanner tasks
    liquid_planner_task_ids = [task.liquid_planner_id for task in tasks_to_timesheet]
    tasks_json = fetch_tasks_by_ids(liquid_planner_task_ids)

    lp_task_ids = [task['id'] for task in tasks_json]
    for task in tasks_to_timesheet:
        try:
            lp_task_index = lp_task_ids.index(task.liquid_planner_id)
        except ValueError:
            print(f'ERROR: Could not find LiquidPlanner task for "{task.label}"')
            # TODO: Do we want to add this to invalid tasks?
            sys.exit(1)

        # This will be set on task objects in all lists as lists contain same object references
        task.set_liquid_planner_task(tasks_json[lp_task_index], member_id)
     
    # Calculate and set shared time multiplier
    total_time = sum([task.get_logged_time_hrs() for task in shared_time_total_tasks])
    total_shared_project_time = 0 if shared_time_project is None else shared_time_project.get_total_task_time()
    shared_time_multiplier = total_time / (total_time - total_shared_project_time)
    
    # Print total daily time
    print(f'\nTotal Task Time: {round(total_time, 2)} hrs')

    # If user has selected to log tasks manually, print valid task total of what is being logged by script
    if len(invalid_tasks) > 0 and not shared_time_on_remaining_tasks:
        invalid_task_time = sum([task.get_logged_time_hrs() for task in invalid_tasks]) * shared_time_multiplier
        valid_task_time = total_time - invalid_task_time
        print(f'\nValid Timesheet Tasks: {round(valid_task_time, 2)} hrs')

    # Print task summary
    for task in tasks_to_timesheet:
        print(f'\t{task.get_print_summary_with_time(shared_time_multiplier, False)}')

    # If user has selected to log tasks manually, print invalid task total and list
    if len(invalid_tasks) > 0 and not shared_time_on_remaining_tasks:
        print(f'\nTasks To Manually Timesheet: {round(invalid_task_time, 2)} hrs')
        for task in invalid_tasks:
            print(f'\t{task.get_print_summary_with_time(shared_time_multiplier, True)}')
    
    # Print shared time summary if time logged
    if total_shared_project_time > 0:
        print(f'\nShared Time Tasks: {round(total_shared_project_time, 2)} hrs ({round(shared_time_multiplier, 2)}x task multiplier)')
        for task in shared_time_project.tasks:
            # Shared time multiplier should not be applied to these tasks
            print(f'\t{task.get_print_summary_with_time(1, True)}')
    
    # Print warnings regarding tasks which have no remaining time
    print()
    for task in tasks_to_timesheet:
        logged_time_hrs = round(task.get_logged_time_hrs() * shared_time_multiplier, 2)
        remaining_time_hrs = task.liquid_planner_remaining_high - logged_time_hrs
        if remaining_time_hrs <= LOW_REMAINING_TIME_WARNING_HRS:
            print(f'WARNING: "{task.label}" has {remaining_time_hrs} hrs remaining')

    # Get confirmation of log output before logging to LiquidPlanner
    print()
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
        activity_id = task.liquid_planner_activity_id or default_activity_id
        body = {
            'work': logged_time_hrs,
            'activity_id': activity_id,
            'low': max(task.liquid_planner_remaining_low - logged_time_hrs, 0),
            'high': max(task.liquid_planner_remaining_high - logged_time_hrs, 0),
            'work_performed_on': post_dt.isoformat()
        }

        try:
            post_timesheet_entry(task.liquid_planner_id, body)
        except Exception:
            print(f'ERROR: Failed to upload timesheet entry for "{task.label}"')

if __name__ == '__main__':
    main()
