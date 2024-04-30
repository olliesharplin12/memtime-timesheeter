## Application Description

This application will extract logged time against tasks in MemTime (TimeBro), and will insert it automatically into LiquidPlanner. Further features and configuration information is described below.

## Setup

#### Script Execution
Mentioned throughout the rest of these instructions are the execution of scripts. It is important to note that these scripts must be executed from a command-line interface which is in the location of the root directory of this repository. This can be done by:

1. Open File Explorer.
2. Navigate to the root directory of this repository.
3. Click your cursor in the blank white space after the final `>` symbol in the navigation bar.
4. Type `cmd` and press enter.
> If done correctly, you will get a command-line interface launch in the root directory of this repository.
5. Type your command and press enter.

> Remember, this will need to be done any time you want to execute one of the scripts below.

#### Installation

1. Ensure Python 3.9 or later is installed and added to PATH.
2. Using the script execution process mentioned above, open a command-line interface in the root directory of this repository.
3. Run command `pip install tzlocal`.
4. Follow instructions in the env.py.template file to allow LiquidPlanner requests to authenticate.

#### Configure Project/Task Structure
1. In MemTime, go to `Project Management` tab and select the settings cog.
2. Under entity creation, select `Project -> Task`.

## MemTime Projects & Tasks

#### Automated MemTime Task Creation
The script `RefreshMemtimeTasks.py` will pull tasks from your upcoming work (My Work) section of LiquidPlanner and will automatically create them in MemTime. When you identify there is a new task in LiquidPlanner which does not exist in MemTime, you can run this script.

However, this only fetches and creates tasks in your upcoming work, which means the tasks need to be added to a priority package in LiquidPlanner (such as a sprint package). There is also a limitation in which tasks which do not have an associated LiquidPlanner project (such as tasks in INBOX) will not be created in MemTime.

To execute:
1. Open a command-line interface in the repository root directory.
2. Run the command `python RefreshMemtimeTasks.py` (run now to populate initial list of tasks).

#### Automated MemTime Task Archiving
The script `ArchiveMemtimeTasks.py` will check your assignments against tasks to see if they have been completed for more than a week. If any are found, these tasks will be archived. This will remove them from your visible task list in MemTime, which is useful as after a while this list will grow quite large.

To execute:
1. Open a command-line interface in the repository root directory.
2. Run the command `python ArchiveMemtimeTasks.py`.

#### Shared Time Project
When executing the `RefreshMemtimeTasks.py` script, a shared time project and task will be automatically created. This can be used for logging time for things such as checking emails, doing your timesheet and taking breaks. Any tasks within this project will have their daily logged time spread across other tasks worked on that day, split by % of the total time.

You can also manually create additional tasks within this shared time project. This can be useful if you want to have more visibility on how much time you are logging to specific shared time areas of your day.

#### Creating Your Own Projects and Tasks in MemTime
You can create your own tasks in MemTime if you wish. This can sometimes be easier if the `RefreshMemtimeTasks.py` script is not creating your task due to it not being high enough priority to be in your upcoming tasks list.

Follow the steps below to create a task manually:
1. If the task you are creating does not belong in an existing project, create the project first. This can be done in the `Project Management` tab in MemTime.
2. In the `Project Management` tab in MemTime, create a new task. Ensure you select a parent project for the task.

#### Mapping MemTime Projects and Tasks to LiquidPlanner

> Note: This process is done automatically when using the `RefreshMemtimeTasks.py` script.

In order to automatically log timesheet information to LiquidPlanner, a reference to a LiquidPlanner task must be stored in the MemTime task. You ***DO NOT*** have to complete this process, as there is an option during execution of the `Timesheet.py` script which allows you to timesheet time for unmapped tasks manually (more on this below). Follow the steps below to link this manually.

1. Open the project or task in LiquidPlanner.
2. Copy the LiquidPlanner ID or URL of the project/task. This can be done in the top-right section of the page by pressing the `Share` button.
3. In the `Project Management` tab in MemTime, select the edit option for the project/task.
4. Paste the LiquidPlanner ID or URL into the `Description` field. Ensure there is nothing else in this field except the pasted value.
5. Select `Save`.

> Note: When executing the `Timesheet.py` script, you will get an warning if you have completed the linking process incorrectly. Come back and review these steps if necessary.

## Timesheet Script Execution

> Before executing this script, it is recommended to read the below sections describing key features of the application.

1. Open a command-line interface in the repository root directory.
2. Run the command `python Timesheet.py`.
3. Answer the prompts where necesary.
4. Open the `Timesheet` tab in LiquidPlanner ([here](https://app.liquidplanner.com/space/164559/timesheet)) and filter the task list by the current day. From here, it is important you review the logged/remaining time on these tasks and add timesheet notes.

Most features within the script are described during its execution, but see below for some features which need a further description.

#### Skip Timesheeting Tasks

If any tasks do not have a valid LiquidPlanner ID or URL in their description fields, you will be prompted if you want to skip timesheeting them. From here you have two options:

- Answer `n` and cancel the script. From here you will need to go into MemTime and fix the LiquidPlanner connection.
- Answer `y` and continue.

If you choose to continue, you will be prompted if you want to split shared time across the remaining tasks, or choose to timesheet the invalid task(s) manually. This decision primarily affects how the shared project time is spread over the tasks.

- If you choose to split the time across remaining tasks (`spl`), this means you are essentially ignoring logging time for the invalid task(s) altogether. I would presume this will not be very commonly used, but some may find it useful.

- If you choose to log invalid tasks manually (`man`), this means the shared time will be split across all tasks as if all tasks were valid. This is useful when you don't want to setup the MemTime to LiquidPlanner connection for a task (maybe because it is only something you are doing for one day). When you get your timesheet output summary, take note of this and use the provided time value to log time against a task of your choice in LiquidPlanner.
