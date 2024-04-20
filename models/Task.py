from typing import List
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

    def set_liquid_planner_task(self, member_id, default_activity_id, task_json):
        self.liquid_planner_crumbs = task_json['parent_crumbs']
        self.liquid_planner_name = task_json['name']

        assigned = False
        for assignment in task_json['assignments']:
            if assignment['person_id'] == member_id:
                self.liquid_planner_activity_id = assignment['activity_id']
                self.liquid_planner_remaining_low = assignment['low_effort_remaining']
                self.liquid_planner_remaining_high = assignment['high_effort_remaining']
                assigned = True
                break
        
        if not assigned:
            self.liquid_planner_activity_id = default_activity_id
            self.liquid_planner_remaining_low = 0
            self.liquid_planner_remaining_high = 0
    
    def get_print_summary(self, shared_time_multiplier: float, ignore_lp_task: bool) -> str:
        logged_time_str = f'{str(round(self.get_logged_time_hrs() * shared_time_multiplier, 2)).ljust(4)} hrs'
        if ignore_lp_task:
            return f'{logged_time_str} | {self.label}'
        else:
            lp_task_label = ' > '.join(self.liquid_planner_crumbs[1:] + [self.liquid_planner_name])
            return f'{logged_time_str} | {self.label} ---> {lp_task_label}'
    
    def __str__(self):
        return f'{self.id}, {self.label}, {self.liquid_planner_url}, {len(self.timesheet_entries)} timesheet entries totalling {self.get_logged_time_hrs()} hrs'
