import datetime
from typing import List, Union

from models.TimesheetEntry import TimesheetEntry
from utils.Util import parse_liquid_planner_id

class Task:
    def __init__(self, id: int, label: str, description: str, parent_id: int, is_active: bool):
        self.id = id
        self.label = label
        self.liquid_planner_id = parse_liquid_planner_id(description)
        self.parent_id = parent_id
        self.is_active = is_active

        self.timesheet_entries: List[TimesheetEntry] = []
    
    def add_entry(self, entry: TimesheetEntry):
        self.timesheet_entries.append(entry)
    
    def get_logged_time_hrs(self) -> float:
        return sum([entry.get_entry_time_hrs() for entry in self.timesheet_entries])

    def set_liquid_planner_task(self, task_json: dict, member_id: int):
        self.liquid_planner_crumbs = task_json['parent_crumbs']
        self.liquid_planner_name = task_json['name']

        self.assignment: Union[dict, None] = None
        self.liquid_planner_activity_id: Union[int, None] = None
        self.liquid_planner_remaining_low: float = 0.0
        self.liquid_planner_remaining_high: float = 0.0
        try:
            self.assignment = [assignment for assignment in task_json['assignments'] if assignment['person_id'] == member_id][0]
        except:
            return

        self.liquid_planner_activity_id: int = self.assignment['activity_id']
        self.liquid_planner_remaining_low: float = self.assignment['low_effort_remaining']
        self.liquid_planner_remaining_high: float = self.assignment['high_effort_remaining']
    
    def is_expired(self, expiry_date: datetime.datetime) -> bool:
        # If self.assignment is None, it is likely this task has changed ownership to another user
        if self.assignment is None:
            return True
        else:
            return self.assignment['is_done'] and self.assignment['done_on'] < expiry_date.isoformat()
    
    def get_print_summary(self, ignore_lp_task: bool) -> str:
        if ignore_lp_task:
            return self.label
        else:
            lp_task_label = ' > '.join(self.liquid_planner_crumbs[1:] + [self.liquid_planner_name])
            return f'{self.label} ---> {lp_task_label}'
    
    def get_print_summary_with_time(self, shared_time_multiplier: float, ignore_lp_task: bool) -> str:
        logged_time_str = f'{str(round(self.get_logged_time_hrs() * shared_time_multiplier, 2)).ljust(4)} hrs'
        return f'{logged_time_str} | {self.get_print_summary(ignore_lp_task)}'
    
    def __str__(self):
        return f'{self.id}, {self.label}, {self.liquid_planner_url}, {len(self.timesheet_entries)} timesheet entries totalling {self.get_logged_time_hrs()} hrs'
