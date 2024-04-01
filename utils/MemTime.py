import sqlite3
import json
import os
from typing import List

from models.TimesheetEntry import TimesheetEntry
from models.Project import Project
from models.Task import Task
from utils.Util import get_epoch_from_datetime


DATABASE_PATH = os.path.join(os.path.expanduser('~'), 'AppData\\Local\\memtime\\user\\62d87704d32b2e0009546557\\data\\tb-private-local-projects\\connected-app.tb-private-local-projects.db')
ENTITY_PROJECT_TYPE = 'project'
ENTITY_TASK_TYPE = 'task'


def query_time_entries(start_epoch: int, end_epoch: int) -> List[TimesheetEntry]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = '''
        SELECT entity, start, end, timeEntryFields
        FROM timeEntry
        WHERE start >= ? AND start < ? AND end >= ? AND end < ?
    '''

    res = cursor.execute(query, (start_epoch, end_epoch, start_epoch, end_epoch))

    time_entries: List[TimesheetEntry] = []
    for entry in res:
        task_id, start_epoch, end_epoch, body = entry
        entity = json.loads(body)['entity']
        entry = TimesheetEntry(task_id, entity['entityType'], entity['label'], int(start_epoch), int(end_epoch))
        time_entries.append(entry)

    conn.close()
    return time_entries

def query_projects(name: str | None = None) -> List[Project]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    where_clause = 'WHERE type = ?'
    params = [ENTITY_PROJECT_TYPE]
    if name is not None:
        where_clause += ' AND name = ?'
        params += [name]

    query = f'''
        SELECT id, name, description
        FROM entity
        {where_clause}
    '''

    res = cursor.execute(query, params)

    projects: List[Project] = []
    for entity in res:
        id, label, description = entity
        projects.append(Project(id, label, description))

    conn.close()
    return projects

def query_tasks(entity_ids: List[int] = None) -> List[Task]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    where_clause = 'WHERE type = ?'
    params = [ENTITY_TASK_TYPE]
    if entity_ids is not None:
        where_clause += f' AND id in ({','.join(['?'] * len(entity_ids))})'
        params += entity_ids

    query = f'''
        SELECT id, name, description, parentId
        FROM entity
        {where_clause}
    '''

    res = cursor.execute(query, params)

    tasks: List[Task] = []
    for entity in res:
        id, label, liquid_planner_url, parent_id = entity
        task = Task(id, label, liquid_planner_url, parent_id)
        tasks.append(task)
    
    conn.close()
    return tasks

def insert_entity(is_project: bool, parent_id: int | None, name: str, description: str, color: str | None = None) -> int:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    entity_type = ENTITY_PROJECT_TYPE if is_project else ENTITY_TASK_TYPE
    keywords = None
    labels = '[]'
    is_active = 1
    # Uses double-quotes intentionally to match formatting of MemTime DB
    config = str({
        "showActivityField": True,  # TODO: Test these options.
        "showBillableField": True,
        "defaultBillability": "inherit",
        "defaultActivity": None
    })
    created_at = get_epoch_from_datetime()

    values = [parent_id, name, description, color, keywords, labels, is_active, entity_type, config, created_at]
    print(values)

    query = f'''
        INSERT INTO entity (parentId, name, description, color, keywords, labels, isActive, type, config, createdAt)
        VALUES ({','.join(['?'] * len(values))})
    '''

    res = cursor.execute(query, values)
    conn.commit()

    memtime_id = res.lastrowid

    conn.close()
    return memtime_id
