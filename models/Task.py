from typing import List
from models.TimesheetEntry import TimesheetEntry

class Task:
    def __init__(self, id: int, label: str, liquid_planner_url: str, parent_id: int):
        self.id = id
        self.label = label
        self.liquid_planner_url = liquid_planner_url
        self.parent_id = parent_id

        self.liquid_planner_task_id: int = None
        self.timesheet_entries: List[TimesheetEntry] = []
    
    def add_entry(self, entry: TimesheetEntry):
        self.timesheet_entries.append(entry)
    
    def get_logged_time_hrs(self):
        return sum([entry.get_entry_time_hrs() for entry in self.timesheet_entries])
    
    def set_id_from_url(self) -> bool:
        task_id = self.liquid_planner_url.split('/')[-1]
        task_id_int = int(task_id)
        if str(task_id_int) == task_id and len(task_id) in [8, 9]:
            self.liquid_planner_task_id = task_id_int
            return True
        return False

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
    
    def get_print_summary(self, is_shared_task: bool) -> str:
        logged_time_str = f'{str(round(self.get_logged_time_hrs(), 2)).ljust(4)} hrs'
        if is_shared_task:
            return f'{logged_time_str} | "{self.label}" ---> "No Timesheet (Shared Time Task)"'
        else:
            lp_task_label = ' > '.join(self.liquid_planner_crumbs[1:] + [self.liquid_planner_name])
            return f'{logged_time_str} | "{self.label}" ---> "{lp_task_label}"'
    
    def __str__(self):
        return f'{self.id}, {self.label}, {self.liquid_planner_url}, {len(self.timesheet_entries)} timesheet entries totalling {self.get_logged_time_hrs()} hrs'
