import datetime
import sys
from typing import List

from models.Task import Task
from utils.MemTime import query_tasks, query_projects, insert_entity
from utils.LiquidPlanner import fetch_upcoming_tasks, TASK_LINK_URL_FORMAT
from utils.Util import ask_question


DAYS_TO_GET_TASKS = 12

def create_memtime_project(id: int, name: str) -> int:
    return insert_entity(True, None, name, id, '#bbbbbb')  # TODO: Colour

def create_memtime_task(lp_url, name, parent_id: int) -> int:
    return insert_entity(False, parent_id, name, lp_url)

def main():
    upcoming_tasks: List[dict] = []
    task_deadline_str = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=DAYS_TO_GET_TASKS)).strftime('%Y-%m-%dT%H:%M:%S')

    task_batch = fetch_upcoming_tasks(100)
    for task in task_batch:
        assignments = [assignment for assignment in task['assignments'] if assignment['person_id'] == 916262]
        if len(assignments) > 0:
            assignment = assignments[0]
            if assignment['expected_start'] is None or assignment['expected_start'] <= task_deadline_str:
                upcoming_tasks.append(task)
            else:
                break
        else:
            print('WARNING: ' + task['name'] + ' - Assignment not found')
    
    
    memtime_tasks: List[Task] = query_tasks()
    
    tasks_to_create: List[(dict, str)] = []
    print('\nFound matching tasks:')
    for task in upcoming_tasks:
        liquid_planner_url = TASK_LINK_URL_FORMAT.format(task['id'])
        associated_memtime_tasks = [task for task in memtime_tasks if task.liquid_planner_url == liquid_planner_url]

        if len(associated_memtime_tasks) == 0:
            tasks_to_create.append((task, liquid_planner_url))
        elif len(associated_memtime_tasks) == 1:
            # TODO: Rename if name is different?
            print(associated_memtime_tasks[0].label, '->', task['name'])
            pass
        else:
            # TODO: Handle duplicate tasks (future)
            task_names = [task.label for task in associated_memtime_tasks]
            print(f'Warning: Found duplicate MemTime tasks ({', '.join(task_names)})')
    
    # Get Projects
    memtime_projects = query_projects()
    existing_project_ids = [project.liquid_planner_id for project in memtime_projects if project.liquid_planner_id is not None]

    # Create Projects
    print('\nNew projects:')
    projects_from_tasks = set([(task['project_id'], task['parent_crumbs'][1]) for task, _ in tasks_to_create])
    projects_to_create = [(id, name) for id, name in projects_from_tasks if id not in existing_project_ids]
    for id, name in projects_to_create:
        print(id, name)
    
    confirmed = ask_question('\nAre you sure you want to create these new projects?')
    if not confirmed:
        sys.exit(1)

    for id, name in projects_to_create:
        memtime_id = create_memtime_project(id, name)
        print(f'Created project {name} ({id}) -> {memtime_id}')
    
    # Refresh Projects
    memtime_projects = query_projects()
    
    print('\nNew tasks:')
    for task, _ in tasks_to_create:
        # TODO: Create MemTime tasks
        print(task['parent_crumbs'][1], '->', task['name'])
    
    confirmed = ask_question('\nAre you sure you want to create these new tasks?')
    if not confirmed:
        sys.exit(1)

    for task, liquid_planner_url in tasks_to_create:
        memtime_id = create_memtime_task(liquid_planner_url, name)  # TODO: Parent ID
        print(f'Created task {name} ({liquid_planner_url}) -> {memtime_id}')

if __name__ == '__main__':
    main()
