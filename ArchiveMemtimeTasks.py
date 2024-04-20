from utils.MemTime import query_tasks


def archive_memtime_tasks():
    # Read all Tasks in MemTime and filter active tasks
    active_tasks = [task for task in query_tasks() if task.is_active]

    # Filter LiquidPlanner IDs
    liquid_planner_ids = []
    for task in active_tasks:
        

    # Get All LiquidPlanner Tasks


    # If task done for personal assignment for longer than X days
    # Archive MemTime task




    pass




if __name__ == '__main__':
    archive_memtime_tasks()
