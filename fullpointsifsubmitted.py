"""
Give full points to any submission without a grade for specified course assignment
"""

# TODO Need to look into whether or not this will handle groups
# TODO script should search through ungraded assignments and present list for selection
# TODO how does this script work with rubrics? (ignores rubric and just gives points, I think)

from canvasapi import Canvas
import pyinputplus
import canvas_lib


def select_assignment_object_menu(ungraded_assignments):
    """Select assignment from list of ungraded assignments"""
    
    while True:

        assignment_names = []
        for assignment in ungraded_assignments:
            assignment_names.append(assignment.name)

        if len(assignment_names) == 0:
            print("No ungraded assignments found.")
            print("Select another course.")
            return

        if len(assignment_names) == 1:
            assignment = ungraded_assignments[0]
            print("\n" + "Only one assignment found: " + assignment.name + "\n")
            print("\n" + "Accessing info for assignment " + assignment.name + "\n")
            return assignment
        
        else:
            assignment_prompt_string = "Select assignment to autograde:\n"
            response = pyinputplus.inputMenu(
                assignment_names,
                numbered=True,
                prompt=assignment_prompt_string
            )

            for selected_assignment in ungraded_assignments:
                if selected_assignment.name == response:
                    assignment = selected_assignment
                    print("\n" + "Accessing info for assignment " + assignment.name + "\n")
                    break


def add_points_to_submitted(selected_assignment, course):
    """Add points to all submissions without a grade for selected assignment"""

    # Get reference list of student names
    students = course.get_users(enrollment_type=['student'])
    student_list = []

    for student in students:
        student_dict = {"id": student.id,
                        "name": str(student.name)}
        student_list.append(student_dict)

    # Give max points if student submitted. Based on
    # https://canvasapi.readthedocs.io/en/stable/examples.html#add-n-points-to-all-users-assignments

    points_awarded = selected_assignment.points_possible

    submissions = selected_assignment.get_submissions()

    count = sum(1 for submission in submissions if submission.score is None)

    print(selected_assignment.name + " has " + str(count) + " submissions without a grade.")

    # Check if we should proceed with regrade
    response = pyinputplus.inputYesNo("Proceed with autograding? (yes/no)\n")

    if response == 'no':
        print("No regrade will be performed.")
        return

    # Do actual autograding
    for submission in submissions:

        # Handle an unscored assignment by checking the `score` value for None

        if submission.score is None:

            for student in student_list:
                if student['id'] == submission.user_id:
                    id_match = student

            submission.edit(submission={'posted_grade': points_awarded})

            print(id_match['name'] + " now has a score of " + str(submission.score))

def main():
    """main function to run the script"""
    # Get Canvas API credentials
    api_key, beta_url, prod_url, user_id = canvas_lib.load_canvas_keys()

    api_url = prod_url
    # TODO need to add option to switch between beta & prod

    # Initialize Canvas Object
    canvas = Canvas(api_url, api_key)

    # get currently favorited courses and make a list of course titles
    favorite_courses = canvas_lib.get_favorite_courses(canvas, user_id)
    course_titles = [i.course_code for i in favorite_courses]

    while True:
        # select course
        selected_course = canvas_lib.course_select_menu(course_titles, favorite_courses)

        # Get Course object
        course = selected_course
        print("\n" + "Accessing info for course " + course.name + "\n")

        # Find all assignments with ungraded submissions
        ungraded_assignments = course.get_assignments(bucket="ungraded")

        selected_assignment = select_assignment_object_menu(ungraded_assignments)

        if selected_assignment is not None:
            add_points_to_submitted(selected_assignment, course)

        # Ask if user wants to continue
        response = pyinputplus.inputYesNo("Continue with another course? (yes/no)\n")
        if response == 'no':
            print("Exiting script.")
            break

        


if __name__ == "__main__":
    main()