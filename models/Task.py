import sys
from typing import List
from models.TimesheetEntry import TimesheetEntry

class Task:
    def __init__(self, id: int, label: str, liquid_planner_url: str):
        self.id = id
        self.label = label
        self.timesheet_entries: List[TimesheetEntry] = []
        self.liquid_planner_task_id = self.get_id_from_url(liquid_planner_url)
    
    def add_entry(self, entry: TimesheetEntry):
        self.timesheet_entries.append(entry)
    
    def get_logged_time_hrs(self):
        return sum([entry.get_entry_time_hrs() for entry in self.timesheet_entries])
    
    def get_id_from_url(self, url: str) -> int:
        try:
            task_id = url.split('/')[-1]
            task_id_int = int(task_id)
            if not (str(task_id_int) == task_id and len(task_id) in [8, 9]):
                raise 'Invalid LP task ID'
        except:
            print(f'ERROR: Ensure LiquidPlanner URL in Memtime task description is valid for "{self.label}"')
            sys.exit(1)

        return task_id_int

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
    
    def get_print_summary(self) -> str:
        logged_time_str = f'{str(self.get_logged_time_hrs()).ljust(4)} hrs'
        lp_task_label = ' > '.join(self.liquid_planner_crumbs[1:] + [self.liquid_planner_name])
        return f'{logged_time_str} | "{self.label}" ---> "{lp_task_label}"'
    
    def get_post_task_body(self) -> dict:
        logged_time_hrs = self.get_logged_time_hrs()
        return {
            'work': logged_time_hrs,
            'activity_id': self.liquid_planner_activity_id,
            'low': max(self.liquid_planner_remaining_low - logged_time_hrs, 0),
            'high': max(self.liquid_planner_remaining_high - logged_time_hrs, 0)
        }
    
    def __str__(self):
        return f'{self.id}, {self.label}, {self.liquid_planner_url}, {len(self.timesheet_entries)} timesheet entries totalling {self.get_logged_time_hrs()} hrs'
