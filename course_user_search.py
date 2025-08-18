"""search for specific user across all current courses"""

from canvasapi import Canvas
import pyinputplus
from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator
import canvas_lib

# Load API keys from environment variables
api_key, beta_url, prod_url, user_id = canvas_lib.load_canvas_keys()

# determine if we are using beta or production and report to user - this should really be an arg
api_url = prod_url
style = Style.from_dict({"aaa": "#44ff00"})

#commented out so I can use interactive python
#print_formatted_text(HTML("<aaa>\nUsing host: " + api_url + "</aaa>\n"), style=style)

# Initialize Canvas Object
canvas = Canvas(api_url, api_key)

# get currently favorited courses and make a list of course titles
favorite_courses = canvas_lib.get_favorite_courses(canvas, user_id)
course_titles = [i.course_code for i in favorite_courses]

# make a master list of students from each course
student_master_list = []
for course in favorite_courses:
    students_temp = canvas_lib.get_students(course)
    student_master_list.extend(students_temp)

# process list and combine duplicates with course2 and course3 etc
merged_students = {}

for student in student_master_list:
    user_id = student['id']
    
    if user_id not in merged_students:
        merged_students[user_id] = {
            "name": student["name"],
            "id": student["id"],
            "email": student["email"],
            "avatar_url": student["avatar_url"],
            "courses": [{
                "course_id": student["course_id"],
                "course_name": student["course_name"]
            }]
        }
    else:
        merged_students[user_id]["courses"].append({
            "course_id": student["course_id"],
            "course_name": student["course_name"]
        })

# TODO Save merged_students to file, and when loading, check if file exists and prompt to load or rebuild
# TODO download avatars for each student and save to disk
# TODO use images from CMS for missing avatars
# TODO add a search function to find students by name or email, should be first prompt if database already exists
# TODO search should display their courses (hotlink to each), email address as hotlink, avatar image