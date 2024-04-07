import datetime
import sys
from typing import List, Tuple

from models.Project import Project
from models.Task import Task
from utils.MemTime import query_tasks, query_projects, insert_entity
from utils.LiquidPlanner import fetch_upcoming_tasks, TASK_LINK_URL_FORMAT
from utils.Util import ask_question


MEMBER_ID = 916262
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

def filter_tasks_to_create(upcoming_tasks: List[dict], memtime_tasks: List[Task]) -> List[Tuple[dict, str]]:
    tasks_to_create: List[Tuple[dict, str]] = []
    for task in upcoming_tasks:
        liquid_planner_url = TASK_LINK_URL_FORMAT.format(task['id'])
        associated_memtime_tasks = [task for task in memtime_tasks if task.liquid_planner_url == liquid_planner_url]

        if len(associated_memtime_tasks) == 0:
            tasks_to_create.append((task, liquid_planner_url))
        elif len(associated_memtime_tasks) >= 2:
            task_names = [task.label for task in associated_memtime_tasks]
            print(f'Warning: Found duplicate MemTime tasks ({", ".join(task_names)})')
        # TODO: Unarchive existing task / update name if different?
    
    return tasks_to_create

def map_tasks_to_memtime_project(tasks_to_create: List[Tuple[dict, str]], memtime_projects: List[Project]) -> List[Tuple[dict, str, Project]]:
    valid_tasks_to_create: List[Tuple[dict, str, Project]] = []
    for task, liquid_planner_url in tasks_to_create:
        associated_memtime_projects = [project for project in memtime_projects if project.liquid_planner_id == task['project_id']]
        if len(associated_memtime_projects) == 0:
            print(f'Error: No MemTime project exists with LiquidPlanner ID {task["project_id"]}')
            continue
        elif len(associated_memtime_projects) >= 2:
            print(f'Warning: Found two or more MemTime projects with LiquidPlanner ID {task["project_id"]}')
        
        memtime_project = associated_memtime_projects[0]
        valid_tasks_to_create.append((task, liquid_planner_url, memtime_project))
        
    return valid_tasks_to_create

def create_memtime_project(id: int, name: str) -> int:
    return insert_entity(True, None, name, id, '#bbbbbb')  # TODO: Colour

def create_memtime_task(lp_url: str, name: str, parent_id: int) -> int:
    return insert_entity(False, parent_id, name, lp_url)

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

def confirm_and_create_tasks(tasks_to_create: List[Tuple[dict, str, Project]]):
    print('\nNew tasks:')
    for task, _, memtime_project in sorted(tasks_to_create, key=lambda tup: tup[2].label):
        print(memtime_project.label, '->', task['name'])

    confirmed = ask_question('\nAre you sure you want to create these new tasks?')
    if not confirmed:
        sys.exit(1)

    for task, liquid_planner_url, memtime_project in tasks_to_create:
        memtime_id = create_memtime_task(liquid_planner_url, task['name'], memtime_project.id)
        print(f'Created task {task["name"]} ({liquid_planner_url}) -> {memtime_id}')

def main():
    # Get upcoming LP tasks and existing MemTime tasks
    upcoming_tasks: List[dict] = get_upcoming_tasks(MEMBER_ID, DAYS_TO_GET_TASKS)
    memtime_tasks: List[Task] = query_tasks()
    
    # Map LP tasks to MemTime tasks by LP URL and filter out new tasks to create
    non_existing_tasks = filter_tasks_to_create(upcoming_tasks, memtime_tasks)
    
    # Get MemTime projects and existing LiquidPlanner IDs
    memtime_projects = query_projects()
    existing_project_ids = [project.liquid_planner_id for project in memtime_projects if project.liquid_planner_id is not None]

    # Filter projects to create
    print('\nFiltering projects to create...')
    projects_from_tasks = set([(task['project_id'], task['parent_crumbs'][1]) for task, _ in non_existing_tasks])
    projects_to_create = [(id, name) for id, name in projects_from_tasks if id not in existing_project_ids]
    # TODO: Unarchive existing projects / update name if different?
    
    # Create new projects and refresh list
    if len(projects_to_create) > 0:
        confirm_and_create_projects(projects_to_create)
        memtime_projects = query_projects()

    # Map tasks to MemTime project
    print('\nFiltering tasks to create...')
    tasks_to_create = map_tasks_to_memtime_project(non_existing_tasks, memtime_projects)
    
    # Create new tasks
    if len(tasks_to_create) > 0:
        confirm_and_create_tasks(tasks_to_create)
    else:
        print('No new tasks to create')

if __name__ == '__main__':
    main()
