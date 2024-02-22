"""essay_grader.py - uses the Canvas API to download essay questions for quick grading at the command line"""

import os
from canvasapi import Canvas
import canvas_lib

API_KEY = os.environ['CANVAS_API_KEY']
BETA_URL = os.environ['CANVAS_BETA_URL']
PROD_URL = os.environ['CANVAS_PRODUCTION_URL']
USER_ID = os.environ['CANVAS_USER_ID']

canvas = Canvas(BETA_URL, API_KEY)

courses = canvas_lib.get_current_courses(canvas, USER_ID)

#unfinished....
"""
ungraded_assignments = [course.get_assignments(bucket='ungraded')]

assignments = course.get_assignments(bucket='ungraded')

for assignment in assignments:
    print(assignment)

    '''