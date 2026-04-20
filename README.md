## Application Description

This application will extract logged time against tasks in MemTime (TimeBro), and will insert it automatically into LiquidPlanner. Further features and configuration information is described below.

## Quick Start

#### Setup

1. Download the repository — either clone it with Git or [download a ZIP](https://github.com/infact-ltd/P000-Memtime-LiquidPlanner-Timesheeter/archive/refs/heads/master.zip) and extract it.
2. Install Python 3.9 or later from [python.org/downloads](https://www.python.org/downloads/). During installation, **check the "Add Python to PATH" checkbox**.
3. Double-click **`Setup.bat`** in the repository folder and follow the prompts. This installs dependencies and sets up your LiquidPlanner credentials.

#### Sprint Cycle

1. After each sprint planning session, double-click **`RefreshTasks.bat`** to populate your MemTime tasks from LiquidPlanner.
2. Additionally, it is recommended to double-click **`ArchiveTasks.bat`** to automatically archive completed work to reduce the number of tasks in the Memtime search results.

#### Daily Use

1. Double-click **`Timesheet.bat`** to submit your timesheet.

## How to Use

#### Automated MemTime Task Creation
The `RefreshTasks` script will pull tasks from your upcoming work (My Work) section of LiquidPlanner and will automatically create them in MemTime. This only fetches and creates tasks in your upcoming work, which means the tasks need to be added to a sprint package in LiquidPlanner. There is also a limitation where LiquidPlanner tasks which are not assigned to a project (such as tasks in INBOX) will not be created in MemTime.

#### Creating Your Own Projects and Tasks in MemTime
Often you will find you need to log time to tasks that are not in your sprint package (e.g. project management). In this case, you can create your own tasks in MemTime. In order to automatically log timesheet information to LiquidPlanner, a reference must be stored in the MemTime task.

> If the task you are creating does not belong to an existing Project in Memtime, create the project first. This can be done in the `Project Management` tab in MemTime by selecting (+).

Follow the steps below to create a task manually:

1. In MemTime, either:
    - Click and drag to create a new time entry and then press `Create`
    - OR, in the `Project Management` tab, create a new task by selecting (+)
2. Open the project or task in LiquidPlanner.
3. Copy the task name from LiquidPlanner into Memtime.
4. Set `of Type` to `Task`.
5. Set `in` to the `Project` of your task.
6. Copy the LiquidPlanner URL of the project/task. This can be done in the top-right section of the page by pressing the `Share` button.
7. Paste this into the Memtime description. Ensure there is nothing else in this field except the URL.
8. Press `Save`.

> Note: When executing the `Timesheet.py` script, you will get an warning if you have linked this incorrectly. Come back and review these steps if necessary.

#### Shared Time Project
When executing the `RefreshTasks` script, a shared time project and task will be automatically created. This can be used for logging time for things such as checking emails, doing your timesheet and taking breaks. Any tasks within this `Memtime Project` will have their daily logged time spread across other tasks worked on that day, split by % of the total time.

> Note: You can create additional tasks within this shared time project (e.g. Emails, Breaks, Timesheet). This can be useful if you want to have more visibility on how much time you are logging to specific shared time areas of your day.

#### Skip Timesheeting Tasks

If any tasks do not have a valid LiquidPlanner ID or URL in their description field, you will be prompted if you want to skip timesheeting them. From here you have two options:

- *(Recommended)* Answer `n` and cancel the script. From here you will need to go into MemTime and fix the LiquidPlanner connection.
- Answer `y` and continue.

If you choose to continue, you will be prompted if you want to timesheet the invalid task(s) manually, or ignore this task (which results in the shared time being split across the remaining valid tasks).

- `man`: This is useful when you don't want to setup the MemTime to LiquidPlanner connection for a task (maybe because it is only something you are doing for one day). If you choose to log invalid tasks manually, shared time will be split across all tasks as usual. When you get your timesheet output summary, manually log the provided time for this task directly into LiquidPlanner.

- `spl`: If you choose to split the time across remaining tasks, this means you are essentially ignoring logging time for the invalid task(s). I would presume this will not be very commonly used, but some may find it useful.
