"""
Give full points to any submission without a grade for specified course assignment
"""

# TODO Need to look into whether or not this will handle groups

import json
import os
from canvasapi import Canvas

COURSE_NUMBER = 21519
ASSIGNMENT_NUMBER = 325713

# Get Canvas API credentials
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

data = json.load(open(os.path.join(__location__, 'config.json'), encoding="utf-8"))

api_key = data["canvas"]["access_token"]
api_url = data["canvas"]["beta_host"]
# TODO need to add option to switch between beta & prod


# Initialize Canvas Object
canvas = Canvas(api_url, api_key)


# Get Course object
course = canvas.get_course(COURSE_NUMBER)
print("\n" + "Accessing info for course " + course.name + "\n")

assignment = course.get_assignment(ASSIGNMENT_NUMBER)

# Get reference list of student names
students = course.get_users(enrollment_type=['student'])
student_list = []

for student in students:
    student_dict = {"id": student.id,
                    "name": str(student.name)}
    student_list.append(student_dict)

# Give max points if student submitted. Based on
# https://canvasapi.readthedocs.io/en/stable/examples.html#add-n-points-to-all-users-assignments

points_awarded = assignment.points_possible

submissions = assignment.get_submissions()

count = sum(1 for submission in submissions if submission.score is None)

print(assignment.name + " has " + str(count) + " submissions without a grade.")

# Check if we should proceed with regrade
while True:
    yesno = input("Proceed with autograding? y/n \n")

    if yesno == 'y':
        break
    if yesno == 'n':
        exit()
    if yesno != "y" or yesno != "n":
        print("Please enter y or n")
        continue

# Do actual autograding
for submission in submissions:

    # Handle an unscored assignment by checking the `score` value for None

    if submission.score is None:

        for student in student_list:
            if student['id'] == submission.user_id:
                id_match = student

        submission.edit(submission={'posted_grade': points_awarded})

        print(id_match['name'] + " now has a score of " + str(submission.score))
