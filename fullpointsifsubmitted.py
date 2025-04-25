"""
Give full points to any submission without a grade for specified course assignment
"""

# TODO Need to look into whether or not this will handle groups
# TODO script should search through ungraded assignments and present list for selection
# TODO how does this script work with rubrics?

from canvasapi import Canvas
import canvas_lib

ASSIGNMENT_NUMBER = 467118

# Get Canvas API credentials
api_key, beta_url, prod_url, user_id = canvas_lib.load_canvas_keys()

api_url = prod_url
# TODO need to add option to switch between beta & prod


# Initialize Canvas Object
canvas = Canvas(api_url, api_key)

# get currently favorited courses and make a list of course titles
favorite_courses = canvas_lib.get_favorite_courses(canvas, user_id)
course_titles = [i.course_code for i in favorite_courses]

# select course
selected_course = canvas_lib.course_select_menu(course_titles, favorite_courses)



# Get Course object
course = selected_course
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
