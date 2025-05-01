"""BugBountyPoints.py - script to quickly add points on the bug bounty"""

# TODO add args when calling this script - would be great for opting to use beta URL
# TODO have script check if points were successfully added - does API give a response?

import re
import cmd
from datetime import datetime
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
print_formatted_text(HTML("<aaa>\nUsing host: " + api_url + "</aaa>\n"), style=style)


# Initialize Canvas Object
canvas = Canvas(api_url, api_key)

# get currently favorited courses and make a list of course titles
favorite_courses = canvas_lib.get_favorite_courses(canvas, user_id)
course_titles = [i.course_code for i in favorite_courses]


# General Functions


def user_select(course):
    """Select a user from a menu with autocompletion"""
    # select the user to add points to
    student_prompt_string = "\n\nSelect a student from the list.\n"

    print("Students in selected course: \n\n")

    student_dicts = []
    for student in course.get_users(enrollment_type=["student"]):
        new_dict = {"name": student.name, "id": student.id}
        student_dicts.append(new_dict)
    student_names = [student["name"] for student in student_dicts]

    # format list of names into multiple columns
    cli = cmd.Cmd()
    cli.columnize(student_names)

    def is_in_list(text):
        return text in student_names

    list_validator = Validator.from_callable(
        is_in_list, error_message="Name entered not in list.", move_cursor_to_end=True
    )
    name_completer = WordCompleter(student_names, match_middle=True, ignore_case=True)
    response = prompt(
        student_prompt_string,
        completer=name_completer,
        validator=list_validator,
        validate_while_typing=True,
    )
    # TODO add validation so program doesn't break if I don't select a user correctly

    sel_student_dict = None
    for i in student_dicts:
        if i["name"] == response:
            sel_student_dict = i
            break

    return sel_student_dict


def get_bb_submission_object(course, sel_student_dict):
    """Find the bug bounty submission object from course object and a dict of student info"""
    # get id for bug bounty assignment
    regex_bug = re.compile(".*bug.*", re.IGNORECASE)
    bug_assign_id = None
    for i in course.get_assignments():
        if regex_bug.match(i.name):
            bug_assign_id = i.id

    assignment = course.get_assignment(bug_assign_id)
    bb_submission_object = assignment.get_submission(
        sel_student_dict["id"], include=["submission_comments"]
    )

    return bb_submission_object


def ask_point_quantity(sel_student_dict, bb_submission_object):
    """Get quantity of points to add to bug bounty submission object"""
    print(
        "\n"
        + sel_student_dict["name"]
        + "'s score for the Bug Bounty is "
        + str(bb_submission_object.score)
        + "."
    )

    print("\nPrior Comments:")
    try:
        for i in bb_submission_object.submission_comments:
            print(
                str(datetime.strptime(i["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
                + ": "
                + i["comment"]
            )
    except AttributeError:
        print("\nNo prior comments.")

    points_to_add = pyinputplus.inputInt(
        prompt="\nHow many points should be added?\n", min=1, max=5
    )

    return points_to_add


def ask_comment_text():
    """Get comment text to add to bug bounty submission object"""
    comment = pyinputplus.inputYesNo(
        prompt="Would you like to add a comment to the submission?\n"
    )
    match comment:
        case "yes":
            comment_text = pyinputplus.inputStr(prompt="Enter your comment:\n")
            return comment_text
        case "no":
            comment_text = ""

    return comment_text


def confirm_add_points(points_to_add, bb_submission_object, comment):
    """confirm if previously chosen point quantity should be added to bb item"""
    choices = ["Yes", "Change points", "Go to course selection"]

    if comment != "":
        prompt_string = (
            "Are you sure you wish to add "
            + str(points_to_add)
            + " points and the following comment?\n"
            + comment
            + "\n"
        )
    else:
        prompt_string = (
            "Are you sure you wish to add " + str(points_to_add) + " points?\n"
        )

    confirm_choice = pyinputplus.inputMenu(
        prompt=prompt_string,
        choices=choices,
        numbered=True,
    )

    match confirm_choice:
        case "Yes":
            canvas_lib.change_submission_points(
                bb_submission_object, points_to_add, comment
            )

            return 1

        case "Change points":
            return 2

        case "Go to course selection":
            return 3


def add_more_points_prompt():
    """Should we go back to beginning of main while loop?"""
    confirm = pyinputplus.inputYesNo(prompt="Add more bug bounty points?\n")
    match confirm:
        case "yes":
            return False

        case "no":
            exit()


def main():
    """Adds points to bug bounty submission after selections by user"""
    continue_main_loop = True

    while continue_main_loop:
        selected_course = canvas_lib.course_select_menu(course_titles, favorite_courses)

        sel_student_dict = user_select(selected_course)

        bb_submission_object = get_bb_submission_object(
            selected_course, sel_student_dict
        )

        continue_point_loop = True

        while continue_point_loop:
            points_to_add = ask_point_quantity(sel_student_dict, bb_submission_object)
            comment = ask_comment_text()

            match confirm_add_points(points_to_add, bb_submission_object, comment):
                case 1:
                    continue_point_loop = add_more_points_prompt()
                case 2:
                    continue
                case 3:
                    break


if __name__ == "__main__":
    main()
