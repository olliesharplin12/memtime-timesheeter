from typing import List
from models.Task import Task

class Project:
    def __init__(self, id: int, label: str):
        self.id = id
        self.label = label
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)
    
    def get_task_ids(self) -> List[int]:
        return [task.id for task in self.tasks]

    def get_total_task_time(self) -> int:
        return sum([task.get_logged_time_hrs() for task in self.tasks])
