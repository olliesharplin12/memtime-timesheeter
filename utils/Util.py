import datetime
import tzlocal
import sys
from typing import Union

def ask_question(question: str, yes_char: str = 'y', no_char: str = 'n') -> bool:
    while True:
        res = input(f'{question} [{yes_char}/{no_char}]: ').lower()
        if res == yes_char.lower():
            return True
        elif res == no_char.lower():
            return False

def get_epoch_from_datetime(dt: datetime.datetime = None) -> int:
    if dt is None:
        date_time = datetime.datetime.now(datetime.timezone.utc)
        epoch_time = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, datetime.timezone.utc)
        timezone_offset_secs = 0
    else:
        date_time = dt
        epoch_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
        timezone_offset_secs = -int(date_time.astimezone(tzlocal.get_localzone()).utcoffset().total_seconds())
    return round((date_time - epoch_time).total_seconds() + timezone_offset_secs)

def parse_liquid_planner_id(description: str) -> Union[int, None]:
    try:
        if len(description) <= 9:
            task_id_str = description
        else:
            task_id_str = description.split('/')[-1]
            if task_id_str[-1] == 'P':
                task_id_str = task_id_str[:-1]

        task_id = int(task_id_str)
        if str(task_id) == task_id_str and len(task_id_str) in [8, 9]:
            return task_id
        return None
    except:
        return None

def exit(code: int):
    input('\nPress enter to close...')
    sys.exit(code)
