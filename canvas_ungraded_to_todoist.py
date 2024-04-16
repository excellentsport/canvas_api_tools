"""
canvas_ungraded_to_todoist.py - looks for ungraded items in Canvas and adds
them to Todoist if they don't exist. Updates ungraded count in task description
if different, and bumps tasks priority when due date arrives.
"""


from sys import platform
import os
from datetime import datetime, timezone, timedelta
import re
from canvasapi import Canvas
from todoist_api_python.api import TodoistAPI


# get keys, td_api endpoints etc
if platform == "ios":
    import keychain

    USER_ID = int(keychain.get_password("CANVAS_USER_ID", "a"))
    API_KEY = keychain.get_password("CANVAS_API_KEY", "a")
    PROD_URL = keychain.get_password("CANVAS_PRODUCTION_URL", "a")
    BETA_URL = keychain.get_password("CANVAS_BETA_URL", "a")
    TD_KEY = keychain.get_password("todoist_api_key", "a")

if platform == "windows" or "win32":
    API_KEY = os.environ["CANVAS_API_KEY"]
    BETA_URL = os.environ["CANVAS_BETA_URL"]
    PROD_URL = os.environ["CANVAS_PRODUCTION_URL"]
    USER_ID = os.environ["CANVAS_USER_ID"]
    TD_KEY = os.environ["TODOIST_API_KEY"]


def get_ungraded_assignments(courses):
    """takes list of canvas course objects to find ones with ungraded items"""
    ungraded_items_list = []
    list_item = 0

    for count, course in enumerate(courses):
        assignments = courses[count].get_assignments(bucket="ungraded")
        for assignment in assignments:
            list_item += 1

            ungraded_items_list.append(
                {"item_number": list_item, "course": course, "assignment": assignment}
            )
    return ungraded_items_list


def get_current_courses(canvas_object, user_id, max_age=250):
    """Output a list of active courses from the Canvas Object younger than max_age days"""

    courses = canvas_object.get_user(user_id).get_courses(
        enrollment_type="teacher", state="available"
    )

    recent_courses = [
        course
        for course in courses
        if (datetime.now(timezone.utc) - course.created_at_date).days < max_age
    ]

    return recent_courses


def build_course_ref(course_list):
    """Takes a list of course objects to build a list of dicts with course id and name"""

    course_ref_list = []
    for course in course_list:
        course_ref_dict = {
            "course_id": course.id,
            "course_name": course.name
        }
        course_ref_list.append(course_ref_dict)

    return course_ref_list


def get_ungraded_metadata(assignment_object, course_ref_list):
    """puts basic metadata from Canvas assignment object into a dictionary"""

    speedgrader_url = (
        "https://csumb.instructure.com/courses/"
        + str(assignment_object.course_id)
        + "/gradebook/speed_grader?assignment_id="
        + str(assignment_object.id)
    )

    ungraded_string = (
        str(assignment_object.needs_grading_count)
        + " ungraded items as of: "
        + str(datetime.now().replace(microsecond=0))
    )

    # make task name with course prefix
    course_prefix = list(
        filter(
            lambda course_ref_list: course_ref_list["course_id"]
            == assignment_object.course_id,
            course_ref_list,
        )
    )[0]["course_name"][:6]
    assignment_task_name = course_prefix + " " + assignment_object.name

    ungraded_dict = {
        "name": assignment_object.name,
        "task_name": assignment_task_name,
        "course_id": assignment_object.course_id,
        "url": assignment_object.html_url,
        "speedgrader_url": speedgrader_url,
        "id": assignment_object.id,
        "count": assignment_object.needs_grading_count,
        "ungraded_string": ungraded_string
    }

    # handle items without due dates correctly
    if hasattr(assignment_object, "due_at_date"):
        ungraded_dict.update({"due": assignment_object.due_at_date})
    else:
        new_due_date = datetime.fromisoformat(assignment_object.updated_at) + timedelta(days=10)
        ungraded_dict.update({"due": new_due_date})

    return ungraded_dict


def task_exists(search_name, td_tasks_list):
    """checks if assignment name can be found in active TD tasks"""

    for i in td_tasks_list:
        if search_name in i.content:
            return i


def make_grading_todo(item_dict, td_api_object):
    """adds todoist item from ungraded item dictionary"""

    try:
        task = td_api_object.add_task(
            content="Grade "
            + item_dict["task_name"]
            + " [Speedgrader Link]("
            + item_dict["speedgrader_url"]
            + ")",
            priority=2,
            description=item_dict["ungraded_string"],
        )
        print("\nCreated New item:")
        print(task)
    except Exception as error:
        print(error)


def update_ungraded_count(item_dict, td_task_object, td_api_object):
    """adds current ungraded count to description if
    different than last reported value in todoist task"""

    new_description = item_dict["ungraded_string"] + "\n" + td_task_object.description

    try:
        is_success = td_api_object.update_task(
            task_id=td_task_object.id, description=new_description
        )
        print("\nUpdated Number to grade for:")
        print(is_success)
    except Exception as error:
        print(error)


def adjust_priority_after_due(item_dict, td_task_object, td_api_object):
    """bump priority of grading items after assignment due date"""

    difference = item_dict["due"].timestamp() - datetime.now().timestamp()

    if difference < 0 and td_task_object.priority < 3:
        try:
            is_success = td_api_object.update_task(task_id=td_task_object.id, priority=3)
            print("\nBumped priority for:")
            print(is_success)
        except Exception as error:
            print(error)


def mark_task_complete_no_items(td_tasks, ungraded_list_canvas, td_api):
    """check td grading tasks against ungraded canvas items; mark as complete if not found"""

    ass_id_list = [x["id"] for x in ungraded_list_canvas]

    for i in td_tasks:
        if "Speedgrader Link" in i.content:
            ass_id = int(re.search(r'(?<=assignment_id=)[0-9]*', i.content)[0])
            if ass_id not in ass_id_list:
                print(ass_id)
                try:
                    is_success = td_api.close_task(task_id=i.id)
                    print(is_success)
                except Exception as error:
                    print(error)
            else:
                continue


def main():
    """tie it all together..."""

    # Get everything needed from the Canvas side
    canvas = Canvas(PROD_URL, API_KEY)

    courses = get_current_courses(canvas, USER_ID)

    course_ref_list = build_course_ref(courses)

    global ungraded_items  # only needed for debugging & development
    ungraded_items = get_ungraded_assignments(courses)

    # pare down huge ungraded_items object into cleaner, simpler list of dicts
    global ungraded_list  # only needed for debugging & development
    ungraded_list = []
    for i in ungraded_items:
        ungraded_list.append(get_ungraded_metadata(i["assignment"], course_ref_list))

    # get all Todoist Task Objects into a list
    td_api = TodoistAPI(TD_KEY)

    try:
        td_tasks = td_api.get_tasks()
    except Exception as error:
        print(error)

    for assignment in ungraded_list:

        # check if there is a Todoist task matching the ungraded item's name
        existing_td_task = task_exists(assignment["task_name"], td_tasks)

        # if task doesn't exist, create it
        if not existing_td_task:
            make_grading_todo(assignment, td_api)

        # if task exists but has different number to grade than
        # indicated by Canvas, then update task description
        # TODO This isn't all that robust - it will goof up
        # TODO with partial matches, i.e. "2" is in "20"

        elif str(assignment["count"]) not in existing_td_task.description[:5]:
            update_ungraded_count(assignment, existing_td_task, td_api)

        # if it's past the assignment's due date, bump up grading priority
        if existing_td_task:
            adjust_priority_after_due(assignment, existing_td_task, td_api)

    mark_task_complete_no_items(td_tasks, ungraded_list, td_api)


if __name__ == "__main__":
    main()
