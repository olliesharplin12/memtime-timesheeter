import sqlite3
import json
import os
from typing import List

from models.TimesheetEntry import TimesheetEntry
from models.Project import Project
from models.Task import Task
from utils.Util import get_epoch_from_datetime


# TODO: User ID is wrong
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

def query_projects(name: str = None) -> List[Project]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    where_clause = 'WHERE type = ?'
    params = [ENTITY_PROJECT_TYPE]
    if name is not None:
        where_clause += ' AND name = ?'
        params += [name]

    query = f'''
        SELECT id, name, description, isActive
        FROM entity
        {where_clause}
    '''

    res = cursor.execute(query, params)

    projects: List[Project] = []
    for entity in res:
        id, label, description, is_active_int = entity
        is_active = is_active_int == 1
        projects.append(Project(id, label, description, is_active))

    conn.close()
    return projects

def query_tasks(entity_ids: List[int] = None) -> List[Task]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    where_clause = 'WHERE type = ?'
    params = [ENTITY_TASK_TYPE]
    if entity_ids is not None:
        where_clause += f' AND id in ({",".join(["?"] * len(entity_ids))})'
        params += entity_ids

    query = f'''
        SELECT id, name, description, parentId, isActive
        FROM entity
        {where_clause}
    '''

    res = cursor.execute(query, params)

    tasks: List[Task] = []
    for entity in res:
        id, label, liquid_planner_url, parent_id, is_active_int = entity
        is_active = is_active_int == 1
        task = Task(id, label, liquid_planner_url, parent_id, is_active)
        tasks.append(task)
    
    conn.close()
    return tasks

def insert_entity(is_project: bool, parent_id: int, name: str, description: str, color: str = None) -> int:
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

    query = f'''
        INSERT INTO entity (parentId, name, description, color, keywords, labels, isActive, type, config, createdAt)
        VALUES ({','.join(['?'] * len(values))})
    '''

    res = cursor.execute(query, values)
    conn.commit()

    memtime_id = res.lastrowid

    conn.close()
    return memtime_id

def set_entity_name(id: int, name: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    values = [name, id]

    query = f'''
        UPDATE entity
        SET name = ?
        WHERE id = ?
    '''

    _ = cursor.execute(query, values)
    conn.commit()
    conn.close()

def set_entity_is_active(id: int, is_active: bool):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    is_active_value = 1 if is_active else 0
    values = [is_active_value, id]

    query = f'''
        UPDATE entity
        SET isActive = ?
        WHERE id = ?
    '''

    _ = cursor.execute(query, values)
    conn.commit()
    conn.close()
