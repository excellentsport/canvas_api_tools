from sys import platform
from canvasapi import Canvas
from todoist_api_python.api import TodoistAPI
import os
from datetime import datetime, timezone

# get keys, api endpoints etc
if platform == 'ios':
    import keychain
    USER_ID = int(keychain.get_password('CANVAS_USER_ID','a'))
    API_KEY = keychain.get_password('CANVAS_API_KEY','a')
    PROD_URL = keychain.get_password('CANVAS_PRODUCTION_URL','a')
    BETA_URL = keychain.get_password('CANVAS_BETA_URL','a')
    TD_KEY = keychain.get_password("todoist_api_key", "a")

if platform == 'windows' or 'win32':
    API_KEY = os.environ['CANVAS_API_KEY']
    BETA_URL = os.environ['CANVAS_BETA_URL']
    PROD_URL = os.environ['CANVAS_PRODUCTION_URL']
    USER_ID = os.environ['CANVAS_USER_ID']
    TD_KEY = os.environ['TODOIST_API_KEY']


def get_ungraded_assignments(courses):
    """takes list of canvas course objects to find ones with ungraded items"""
    ungraded_items_list = []
    list_item = 0

    for count, course in enumerate(courses):
        assignments = courses[count].get_assignments(bucket="ungraded")
        for assignment in assignments:
            list_item += 1
            
            ungraded_items_list.append({
             "item_number": list_item,
             "course": course,
             "assignment": assignment
            })
    return ungraded_items_list


def get_current_courses(canvas_object, user_id, max_age=250):
    """Output a list of active courses from the Canvas Object younger than max_age days"""

    courses = canvas_object.get_user(user_id).get_courses(
     enrollment_type="teacher", state="available")

    recent_courses = [
     course for course in courses
     if (datetime.now(timezone.utc) - course.created_at_date).days < max_age
    ]

    return recent_courses
    
def get_ungraded_metadata(assignment_object):
    """puts basic metadata from Canvas assignment object into a dictionary"""
    
    # https://csumb.instructure.com/courses/23480/gradebook/speed_grader?assignment_id=360182&student_id=27274
    
    speedgrader_url = 'https://csumb.instructure.com/courses/'\
        + str(assignment_object.course_id)\
        + '/gradebook/speed_grader?assignment_id='\
        + str(assignment_object.id)
    
    ungraded_string = str(assignment_object.needs_grading_count)\
    + " ungraded items as of: "\
    + str(datetime.now().replace(microsecond=0))
        
    ungraded_dict = {
        'name': assignment_object.name,
        'url': assignment_object.html_url,
        'speedgrader_url': speedgrader_url,
        'id': assignment_object.id,
        'count': assignment_object.needs_grading_count,
        'ungraded_string': ungraded_string,
        'due': assignment_object.due_at_date
    }
        
    return ungraded_dict
        
def make_grading_todo(item_dict, api_object):
    """adds todoist item from ungraded item dictionary"""

    try:
        task = api_object.add_task(
            content="Grade " 
            + item_dict['name']
            + " [Speedgrader Link]("
            + item_dict['speedgrader_url']
            + ")",
            priority=2,
            description=item_dict['ungraded_string'],
            )
        print("Created New item:")
        print(task)
    except Exception as error:
        print(error)
    

def update_ungraded_count(item_dict, td_task_object, api_object):
    """adds current ungraded count to description if different than last reported value in todoist task"""
    
    new_description = item_dict['ungraded_string']+ '\n' + td_task_object.description
    
    try:
        is_success = api_object.update_task(task_id=td_task_object.id, description= new_description)
        print("\nUpdated Number to grade for:")
        print(is_success)
    except Exception as error:
        print(error)
    ### maybe change task priority if due date has passed?

def task_exists(search_name, api_object):
    """checks if assignment name can be found in active TD tasks"""
    
    try:
        tasks_json = api_object.get_tasks()
    except Exception as error:
        print(error)
        
    for i in tasks_json:
        if search_name in i.content:
            return i
        
def adjust_priority_after_due(item_dict, td_task_object, api_object):
    """bump priority of grading items after assignment due date"""
    difference = item_dict['due'].timestamp() - datetime.now().timestamp()
            
    if difference < 0 and td_task_object.priority < 3:
        try:
            is_success = api_object.update_task(task_id=td_task_object.id, priority=3)
            print("\nBumped priority for:")
            print(is_success)
        except Exception as error:
            print(error)

def main():
    canvas = Canvas(PROD_URL, API_KEY)

    courses = get_current_courses(canvas, USER_ID)

    global ungraded_items
    ungraded_items = get_ungraded_assignments(courses)
    
    global ungraded_list
    ungraded_list =[]
    
    for i in ungraded_items:
        ungraded_list.append(
            get_ungraded_metadata(i['assignment']))
            
    api = TodoistAPI(TD_KEY)
    
    for assignment in ungraded_list:
        existing_td_task = task_exists(assignment['name'], api)
    
        if not existing_td_task:
            make_grading_todo(assignment, api)
        elif str(assignment['count']) not in existing_td_task.description[:5]:
            update_ungraded_count(assignment, existing_td_task, api)
            
        if existing_td_task:
        	adjust_priority_after_due(assignment, existing_td_task, api)
    
    

if __name__ == "__main__":
    main()

