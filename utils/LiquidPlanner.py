import requests
from requests.auth import HTTPBasicAuth

from env import LIQUID_PLANNER_EMAIL, LIQUID_PLANNER_PASSWORD
from requests import Response
from typing import List

WORKSPACE_ID = 164559
BASE_URL = f'https://app.liquidplanner.com/api/v1/workspaces/{WORKSPACE_ID}/'
FETCH_MEMBER_URL_FORMAT = 'members/{0}'
FETCH_TASKS_URL = 'tasks'
FETCH_UPCOMING_TASKS_URL = 'upcoming_tasks'
POST_TIMESHEET_URL_FORMAT = 'treeitems/{0}/track_time'

AUTH = HTTPBasicAuth(LIQUID_PLANNER_EMAIL, LIQUID_PLANNER_PASSWORD)

def build_url(url_suffix: str, query_params: List[tuple[str, str]] = None) -> str:
    if query_params is not None and len(query_params) > 0:
        return BASE_URL + url_suffix + '?' + '&'.join([f'{key}={value}' for key, value in query_params])
    else:
        return BASE_URL + url_suffix

def get(url_suffix: str, query_params: List[tuple[str, str]] = None) -> Response:
    url = build_url(url_suffix, query_params)
    return requests.get(url, auth=AUTH)

def post(url_suffix: str, body: dict) -> Response:
    url = build_url(url_suffix)
    return requests.post(url, data=body, auth=AUTH)

def fetch_my_account() -> dict:
    response = requests.get('https://app.liquidplanner.com/api/v1/account', auth=AUTH)
    if response.status_code != 200:
        raise Exception(f'Response Error: {response.text}')

    return response.json()

def fetch_member(member_id: str) -> dict:
    response = get(FETCH_MEMBER_URL_FORMAT.format(member_id))
    if response.status_code != 200:
        raise Exception(f'Response Error: {response.text}')

    return response.json()

def fetch_tasks_by_ids(task_ids: List[int]) -> dict:
    query_params: List[tuple[str, str]] = [('filter[]=id', ','.join(map(str, task_ids)))]

    response = get(FETCH_TASKS_URL, query_params)
    if response.status_code != 200:
        raise Exception(f'Response Error: {response.text}')

    return response.json()

def fetch_upcoming_tasks(limit: int) -> dict:
    query_params: List[tuple[str, str]] = [('flat', True), ('limit', limit)]

    response = get(FETCH_UPCOMING_TASKS_URL, query_params)
    if response.status_code != 200:
        raise Exception(f'Response Error: {response.text}')

    return response.json()

def post_timesheet_entry(task_id: int, body: dict):
    post_url = POST_TIMESHEET_URL_FORMAT.format(task_id)
    response = post(post_url, body)
    if response.status_code != 200:
        raise Exception(f'Response Error: {response.text}')

    return response.json()
