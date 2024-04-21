import datetime
import sys
from typing import List, Tuple

from models.Project import Project
from models.Task import Task
from utils.MemTime import query_tasks, query_projects, insert_entity, set_entity_is_active, set_entity_name
from utils.LiquidPlanner import fetch_my_account, fetch_upcoming_tasks
from utils.Util import ask_question


DAYS_TO_GET_TASKS = 12

def get_upcoming_tasks(member_id: int, days_to_get_tasks: int):
    upcoming_tasks: List[dict] = []
    task_deadline_str = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_to_get_tasks)).strftime('%Y-%m-%dT%H:%M:%S')
    task_batch = fetch_upcoming_tasks(100)
    
    for task in task_batch:
        assignments = [assignment for assignment in task['assignments'] if assignment['person_id'] == member_id]
        if len(assignments) > 0:
            assignment = assignments[0]
            if assignment['expected_start'] is None or assignment['expected_start'] <= task_deadline_str:
                upcoming_tasks.append(task)
            else:
                break
        else:
            print('WARNING: ' + task['name'] + ' - Assignment not found')

    return upcoming_tasks

def filter_tasks_to_create(member_id: int, upcoming_tasks: List[dict], memtime_tasks: List[Task]) -> Tuple[List[dict], List[Task], List[Task]]:
    tasks_to_create: List[dict] = []
    tasks_to_set_active: List[Task] = []
    tasks_to_rename: List[Task] = []

    for lp_task in upcoming_tasks:
        # Ignore Inbox tasks for now as we won't know which MemTime project to assign them to
        # TODO: Update project when task refetched then allow inbox tasks
        if len(lp_task['parent_crumbs']) < 2:
            continue
        
        associated_memtime_tasks = [task for task in memtime_tasks if task.liquid_planner_id == lp_task['id']]

        if len(associated_memtime_tasks) == 0:
            tasks_to_create.append(lp_task)
            continue
        elif len(associated_memtime_tasks) >= 2:
            task_names = [task.label for task in associated_memtime_tasks]
            print(f'Warning: Found duplicate MemTime tasks ({", ".join(task_names)}). Operations will be performed to both.')
        
        for memtime_task in associated_memtime_tasks:
            memtime_task.set_liquid_planner_task(lp_task, member_id)

            # If an associated task exists but has been archived, add to list to re-activate.
            if not memtime_task.is_active:
                tasks_to_set_active.append(memtime_task)
        
            # If an associated task exists but is named differently to LiquidPlanner, add to list to update name.
            if memtime_task.label != lp_task['name']:
                tasks_to_rename.append(memtime_task)
    
    return tasks_to_create, tasks_to_set_active, tasks_to_rename

def map_tasks_to_memtime_project(tasks_to_create: List[dict], memtime_projects: List[Project]) -> List[Tuple[dict, Project]]:
    valid_tasks_to_create: List[Tuple[dict, str, Project]] = []
    for task in tasks_to_create:
        associated_memtime_projects = [project for project in memtime_projects if project.liquid_planner_id == task['project_id']]
        if len(associated_memtime_projects) == 0:
            print(f'Error: No MemTime project exists with LiquidPlanner ID {task["project_id"]}')
            continue
        elif len(associated_memtime_projects) >= 2:
            print(f'Warning: Found two or more MemTime projects with LiquidPlanner ID {task["project_id"]}')
        
        memtime_project = associated_memtime_projects[0]
        valid_tasks_to_create.append((task, memtime_project))
        
    return valid_tasks_to_create

def create_memtime_project(lp_id: int, name: str) -> int:
    return insert_entity(True, None, name, lp_id, '#bbbbbb')  # TODO: Colour

def create_memtime_task(lp_id: int, name: str, parent_id: int) -> int:
    return insert_entity(False, parent_id, name, lp_id)

def confirm_and_create_projects(projects_to_create: List[Tuple[int, str]]):
    print('\nNew projects:')
    for id, name in projects_to_create:
        print(id, name)

    confirmed = ask_question('\nAre you sure you want to create these new projects?')
    if not confirmed:
        sys.exit(1)

    for id, name in projects_to_create:
        memtime_id = create_memtime_project(id, name)
        print(f'Created project {name} ({id}) -> {memtime_id}')

def confirm_and_create_tasks(tasks_to_create: List[Tuple[dict, Project]]):
    print('\nNew tasks:')
    for task, memtime_project in sorted(tasks_to_create, key=lambda tup: tup[1].label):
        print(memtime_project.label, '->', task['name'])

    confirmed = ask_question('\nAre you sure you want to create these new tasks?')
    if not confirmed:
        sys.exit(1)

    for task, memtime_project in tasks_to_create:
        memtime_id = create_memtime_task(task["id"], task['name'], memtime_project.id)
        print(f'Created task {task["name"]} ({task["id"]}) -> {memtime_id}')

def main():
    # Get current member ID
    user_account = fetch_my_account()
    member_id = user_account['id']

    # Get upcoming LP tasks and existing MemTime tasks
    upcoming_tasks: List[dict] = get_upcoming_tasks(member_id, DAYS_TO_GET_TASKS)
    memtime_tasks: List[Task] = query_tasks()
    
    # Map LP tasks to MemTime tasks by LP URL and filter out new tasks to create
    non_existing_tasks, tasks_to_set_active, tasks_to_rename = filter_tasks_to_create(member_id, upcoming_tasks, memtime_tasks)
    
    # Get MemTime projects and existing LiquidPlanner IDs
    memtime_projects = query_projects()
    existing_project_ids = [project.liquid_planner_id for project in memtime_projects if project.liquid_planner_id is not None]

    # Filter projects to create
    print('\nFiltering projects to create...')
    projects_from_tasks = set([(task['project_id'], task['parent_crumbs'][1]) for task in non_existing_tasks])
    projects_to_create = [(id, name) for id, name in projects_from_tasks if id not in existing_project_ids]
    # TODO: Unarchive existing projects / update name if different?
    
    # Create new projects and refresh list
    if len(projects_to_create) > 0:
        confirm_and_create_projects(projects_to_create)
        memtime_projects = query_projects()
    else:
        print('No new projects to create')

    # Map tasks to MemTime project
    print('\nFiltering tasks to create...')
    tasks_to_create = map_tasks_to_memtime_project(non_existing_tasks, memtime_projects)
    
    # Create new tasks
    if len(tasks_to_create) > 0:
        confirm_and_create_tasks(tasks_to_create)
    else:
        print('No new tasks to create')

    # Set projects back to active if archived
    projects_to_set_active: List[Project] = []
    for _, project in tasks_to_create:
        # Check active and prevent duplicates
        if not project.is_active and project.id not in [project.id for project in projects_to_set_active]:
            projects_to_set_active.append(project)

    if len(projects_to_set_active) > 0:
        print()
        for memtime_project in projects_to_set_active:
            set_entity_is_active(memtime_project.id, True)
            print(f'Project "{memtime_project.label}" reactivated')
    
    # Set tasks back to active if archived
    if len(tasks_to_set_active) > 0:
        print()
        for memtime_task in tasks_to_set_active:
            set_entity_is_active(memtime_task.id, True)
            print(f'Task "{memtime_task.label}" reactivated')

    # Rename tasks if name is different
    if len(tasks_to_rename) > 0:
        print('\nTasks to rename:')
        for memtime_task in tasks_to_rename:
            print(f'\t{memtime_task.get_print_summary(False)}')
        
        print()
        rename_tasks = ask_question('Do you want to rename the above tasks?')
        if rename_tasks:
            for memtime_task in tasks_to_rename:
                set_entity_name(memtime_task.id, memtime_task.liquid_planner_name)


if __name__ == '__main__':
    main()
