"""BugBountyPoints.py - script to quickly add points on the bug bounty"""

import json
import os
from canvasapi import Canvas
from datetime import datetime, timezone
import pyinputplus
import re

# TODO build this out with functions, classes etc so that it is more extensible than just the narrow function it current has.

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

data = json.load(open(os.path.join(__location__, 'config.json'), encoding="utf-8"))

api_key = data["canvas"]["access_token"]
api_url = data["canvas"]["prod_host"]
user_id = data["canvas"]["user_id"]

# Initialize Canvas Object
canvas = Canvas(api_url, api_key)

# Get list of current courses I'm teaching
courses = canvas.get_user(user_id).get_courses(enrollment_type="teacher", state='available')

#filter out courses that are older than 120 days
recent_courses = [course for course in courses if (datetime.now(timezone.utc) - course.created_at_date).days < 120]
course_titles = [i.course_code for i in recent_courses]

#select the correct course
course_prompt_string = "Which course are you adding bug bounty points for?\n"
for count, i in enumerate(course_titles): course_prompt_string += str(count+1) + ". " + i + "\n"
response = pyinputplus.inputInt(prompt=course_prompt_string, min=1, max= len(course_titles))
course = recent_courses[int(response)-1]

#select the user to add points to
student_prompt_string = "\n\nSelect a student from the following list:\n"
student_dicts = []
for count, student in enumerate(course.get_users(enrollment_type =['student'])):
    dict = {"name":student.name, "id":student.id}
    student_dicts.append(dict)
student_names = [student["name"] for student in student_dicts]

response = pyinputplus.inputMenu(choices = student_names, prompt=student_prompt_string, numbered=True)

sel_student_dict = None
for i in student_dicts:
    if i["name"] == response:
        sel_student_dict = i
        break

# get id for bug bounty assignment
regex_bug = re.compile(".*bug.*", re.IGNORECASE)
bug_assign_id = None
for i in course.get_assignments():
    if regex_bug.match(i.name):
        bug_assign_id = i.id

points_to_add = pyinputplus.inputInt(prompt = "\nHow many points should be added?\n", min=1, max=5)

assignment = course.get_assignment(bug_assign_id)
submission = assignment.get_submission(sel_student_dict["id"])

print('\n' + sel_student_dict["name"] + "'s score for the Bug Bounty is " + str(submission.score) + ".")
confirm = pyinputplus.inputYesNo(prompt = "Are you sure you wish to add " + str(points_to_add) + " points?\n")

if confirm == "yes":
    if submission.score is not None:
        score = submission.score + points_to_add
    else:
        # Treat no submission as 0 points
        score = 0 + points_to_add

    submission.edit(submission={'posted_grade': score})

    print("Score has been changed to: " + str(submission.score))
else:
    exit()