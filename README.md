## Application Description

This application will read your local computer's MemTime database. The tasks you have created here will have an associated LiquidPlanner URL (follow instructions below to set). This will automatically timesheet your logged work from MemTime directly into the LiquidPlanner task. Further features and configuration information is setup below.

## Requirements

### Installation

1. Ensure Python 3 is installed and added to PATH
2. Run command `pip install tzlocal`
3. Follow instructions in the env.py.template file to allow LiquidPlanner requests to authenticate

### MemTime Configuration

#### Configure Project/Task Structure
1. In MemTime, go to `Project Management` tab and select the settings cog.
2. Under entity creation, select `Project -> Task`.

#### Shared Time Project
This application allows for a shared time project to be created. This allows for logging time for things such as checking emails and doing your timesheet. Any tasks within this project will have their daily logged time spread across other tasks by % of the total time for the day.

Follow the steps below to create the shared time project:
1. Check the `SHARED_TIME_PROJECT_NAME` variable in `main.py` and copy its value.
2. In MemTime, create a project with the same name as the copied value.
3. If you like, you can change the name of the shared project, as long as you copy your chosen project name (case-sensitive) into the `SHARED_TIME_PROJECT_NAME` variable.

#### LiquidPlanner Task Mapping

1. For each `Task` you make, ensure you assign it to a parent `Project` (which represents a project in LiquidPlanner).
2. When you create a new `Task` in MemTime, copy the relevant LiquidPlanner URL of that task and paste that into the `Description` field of the `Task` in MemTime. This can be copied by selecting the `Share` icon in the top right corner of LiquidPlanner. When running the timesheeter, you will get a warning if a Task's matching LiquidPlanner URL has not been configured correctly.
- Note: You cannot submit a daily timesheet with two different MemTime tasks referencing the same LiquidPlanner task. You will get an error when this occurs.

## To Execute

1. Open in Windows terminal in the repository root directory.
2. Run the command `python main.py`.
