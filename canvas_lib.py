"""canvas_lib.py - contains standard functions for interacting with Canvas API"""

import os
from datetime import datetime, timezone
import pyinputplus


def load_canvas_keys():
    """Gets important info from env variables"""
    api_key = os.environ["CANVAS_API_KEY"]
    beta_url = os.environ["CANVAS_BETA_URL"]
    prod_url = os.environ["CANVAS_PRODUCTION_URL"]
    user_id = os.environ["CANVAS_USER_ID"]

    return api_key, beta_url, prod_url, user_id


def get_current_courses(canvas_object, user_id, max_age=250):
    """Output a list of active courses from the Canvas Object younger than max_age days
    ***Deprecated - use get_favorite_courses instead***
    """

    courses = canvas_object.get_user(user_id).get_courses(
        enrollment_type="teacher", state="available"
    )

    recent_courses = [
        course
        for course in courses
        if (datetime.now(timezone.utc) - course.created_at_date).days < max_age
    ]

    return recent_courses


def get_favorite_courses(canvas_object, user_id):
    """Output a list of active courses from the Canvas
    object that are currently saved as favorites"""

    courses = canvas_object.get_user(user_id).get_courses(
        enrollment_type="teacher",
        state="available",
        enrollment_state="active",
        include=["favorites"],
    )

    favorites = [course for course in courses if course.is_favorite is True]

    return favorites


def get_students(course_object):
    """Output a dict of active students in the course object"""

    student_dicts = []

    for student in course_object.get_users(enrollment_type=["student"]):
        new_dict = {
            "name": student.name,
            "id": student.id,
            "email": student.email,
            "course_id": course_object.id,
            "course_name": course_object.name,
        }
        student_dicts.append(new_dict)

    return student_dicts


def change_submission_points(submission_object, points_to_add, comment_text=""):
    """Takes a Canvas submission object and adds points. Optionally add a comment"""
    if submission_object.score is not None:
        score = submission_object.score + points_to_add
    else:
        # Treat no submission as 0 points
        score = 0 + points_to_add

    print("comment_text: ", comment_text)
    # print(dir(submission_object))

    if comment_text != "":
        submission_object.edit(
            submission={"posted_grade": score}, comment={"text_comment": comment_text}
        )
    else:
        submission_object.edit(submission={"posted_grade": score})

    print("\nScore has been changed to: " + str(submission_object.score))
    print("Current comments are:\n")
    for i in submission_object.submission_comments:
        print(
            str(datetime.strptime(i["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
            + ": "
            + i["comment"]
        )

    if comment_text != "":
        print("\nComment has been added to submission.\n")


def course_select_menu(course_titles, courses):
    """Select course from list of courses"""
    # select the correct course
    course_prompt_string = "\nSelect the course you wish to interact with\n"
    for count, i in enumerate(course_titles):
        course_prompt_string += str(count + 1) + ". " + i + "\n"

    response = pyinputplus.inputInt(
        prompt=course_prompt_string, min=1, max=len(course_titles)
    )
    course = courses[int(response) - 1]

    return course
