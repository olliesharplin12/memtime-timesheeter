import datetime
import tzlocal

def ask_question(question: str) -> bool:
    while True:
        res = input(f'{question} [y/n]: ').lower()
        if res == 'y':
            return True
        elif res == 'n':
            return False

def get_epoch_from_datetime(dt: datetime.datetime = None) -> int:
    if dt is None:
        date_time = datetime.datetime.now(datetime.UTC)
        epoch_time = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, datetime.UTC)
        timezone_offset_secs = 0
    else:
        date_time = dt
        epoch_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
        timezone_offset_secs = -int(date_time.astimezone(tzlocal.get_localzone()).utcoffset().total_seconds())
    return round((date_time - epoch_time).total_seconds() + timezone_offset_secs)

def strip_liquid_planner_url(url: str | None) -> str | None:
    if url is not None and url[-1] == 'P':
        return url [:-1]
    return url

def strip_liquid_planner_id(id: str | None) -> int | None:
    if id is None:
        return None
    if id[-1] == 'P':
        id = id[:-1]
    try:
        return int(id)
    except ValueError:
        return None
