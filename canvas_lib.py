"""canvas_lib.py - contains standard functions for interacting with Canvas API"""

from datetime import datetime, timezone


def get_current_courses(canvas_object, user_id, max_age=250):
    """Output a list of active courses from the Canvas Object younger than max_age days"""

    courses = canvas_object.get_user(user_id).get_courses(
        enrollment_type="teacher", state='available')

    recent_courses = [course for course in courses if
                      (datetime.now(timezone.utc) - course.created_at_date).days < max_age]

    return recent_courses


def get_students(course_object):
    """Output a dict of active students in the course object"""

    student_dicts = []

    for student in course_object.get_users(enrollment_type=['student']):
        new_dict = {"name": student.name, "id": student.id}
        student_dicts.append(new_dict)

    return student_dicts
