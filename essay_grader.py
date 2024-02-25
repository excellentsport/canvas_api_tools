"""essay_grader.py - uses the Canvas API to download essay questions for quick grading at the command line"""

from sys import platform

import os
from canvasapi import Canvas
import canvas_lib

#determine platform to ensure env variabkes come from correct source
if platform == 'ios':
	import keychain
	USER_ID = int(keychain.get_password('CANVAS_USER_ID','a'))
	API_KEY = keychain.get_password('CANVAS_API_KEY','a')
	PROD_URL = keychain.get_password('CANVAS_PRODUCTION_URL','a')
	BETA_URL = keychain.get_password('CANVAS_BETA_URL','a')

if platform == 'windows':
	API_KEY = os.environ['CANVAS_API_KEY']
	BETA_URL = os.environ['CANVAS_BETA_URL']
	PROD_URL = os.environ['CANVAS_PRODUCTION_URL']
	USER_ID = os.environ['CANVAS_USER_ID']



canvas = Canvas(BETA_URL, API_KEY)

courses = canvas_lib.get_current_courses(canvas, USER_ID)

ungraded_items_list=[]
list_item = 0
# list all ungraded assignments across courses
for count, course in enumerate(courses):
	assignments = courses[count].get_assignments(bucket='ungraded')
	for assignment in assignments:
		list_item +=1
		print(str(list_item) + '. ' + course.name + ' -- ' + assignment.name)
		ungraded_items_list.append({
			'item_number':list_item,
			'course':course,
			'assignment':assignment
			})

