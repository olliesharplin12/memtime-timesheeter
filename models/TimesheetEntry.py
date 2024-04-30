ENTRY_TIME_DECIMALS = 2

class TimesheetEntry:
    def __init__(self, entity_id: int, entity_type: str, label: str, start: int, end: int):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.label = label
        self.start = start
        self.end = end
    
    def get_entry_time_hrs(self) -> float:
        return round((self.end - self.start) / 60.0 / 60.0, ENTRY_TIME_DECIMALS)

    def __str__(self):
        return f'{self.entity_id}, {self.entity_type}, {self.label}, {self.start}, {self.end}'
