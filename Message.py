import Subject_Management as sm
import Utils
import pandas as pd
from datetime import datetime
from datetime import timedelta
import Redcap as rc
from VisitEntry import VisitEntry


def customize_message(template_str, replacements):
    """
    Customize the given message template by replacing placeholders with the values provided in 'replacements'.
    
    :param template_str: The message template as a string, containing placeholders like {placeholder_name}.
    :param replacements: A dictionary where keys are placeholder names and values are the corresponding replacements.
    :return: A string containing the customized message.
    """
    try:
        # Use the format method for substitution, unpacking the replacements dictionary
        customized_content = template_str.format(**replacements)
        return customized_content
    except KeyError as e:
        print(f"A placeholder was not provided a replacement: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def read_text_file(file_path):
    """
    Read a text file and return its content as a string.
    
    :param file_path: The path to the text file to be read.
    :return: A string containing the text of the document.
    """
    try:
        # Open and read the text file
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def read_xlsx(filepath, sheet_name=0):
    """
    Reads an xlsx file and returns a pandas DataFrame object.

    Args:
      filepath (str): The path to the xlsx file.
      sheet_name (int or str, optional): The sheet name or index to read. Defaults to 0 (first sheet).

    Returns:
      pandas.DataFrame: The DataFrame object containing the data from the xlsx file.
    """
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        return df
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except pd.errors.ParserError as e:
        print(f"Error parsing Excel file: {e}")
    return None


def gen_safe_string(list):
    return ';;'.join(list)


def format_list_with_numbers(items):
    """
    Add line numbering to all elements, excluding the first, last, and second to last items
    """

    if len(items) > 4:
        # Iterate over the list from the second element to the second to last element (exclusive)
        for i in range(1, len(items) - 3):
            # Modify the element by prepending the index (i starts from 0, so i+1 gives the number starting from 1)
            items[i] = f"{i}. {items[i]}"

    return gen_safe_string(items)


def build_dupi_message(sdf, subject_id, who_addressed):
    subject_data = sm.filter_by_id(sdf, subject_id)
    subject_week = Utils.get_clean_df_value(subject_data['Week'])

    msg_blocks = []
    dupi_link = rc.get_survey_link(sdf, subject_id, subject_week, who_addressed, 'dupi_survey')
    if who_addressed == "Proxy":
        subject_address = Utils.get_clean_df_value(subject_data['Proxy address'])
    else:
        subject_address = Utils.get_clean_df_value(subject_data['Subject address'])

    msg_blocks.append(f'Hi {subject_address}! Just a reminder a dupilumab injection is due today.')
    msg_blocks.append(f'Please fill out this survey afterwards: {dupi_link}')

    # Thank you block
    msg_blocks.append("")
    msg_blocks.append("Please reach out with any questions. Thank you!!")
    msg_blocks.append("-Brian")

    msg = gen_safe_string(msg_blocks)
    print(Utils.unsafe_string(msg))
    return msg


# who_addressed can be proxy or subject
def build_message(sdf, subject_id, who_addressed, target_date):
    """
    Generate and print customized messages for a list of users based on multiple criteria.
    Also, handle to-do list reminders for each user.
    """
    subject_data = sm.filter_by_id(sdf, subject_id)
    subject_name = Utils.get_clean_df_value(subject_data['First name'])
    subject_initials = Utils.get_clean_df_value(subject_data['Initials'])
    subject_age = Utils.get_clean_df_value(subject_data['Age'])
    subject_id_raw = Utils.get_clean_df_value(subject_data['Subject'])
    subject_id = f'{subject_id_raw:02}'
    subject_enrollment_date = Utils.get_clean_df_value(subject_data['Enroll date'])
    week_extensions = Utils.get_clean_df_value(subject_data['Week extensions'])
    subject_week = sm.calculate_study_week(subject_enrollment_date, target_date, week_extensions)

    if who_addressed == 'Proxy':
        if subject_age >= 8:
            link1 = rc.get_survey_link(sdf, subject_id, subject_week, 'Proxy')
            link2 = rc.get_survey_link(sdf, subject_id, subject_week, 'Subject')
        else:
            link1 = rc.get_survey_link(sdf, subject_id, subject_week, 'Proxy')
    else:
        link1 = rc.get_survey_link(sdf, subject_id, subject_week, 'Subject')

    # Get info about the next appoinment
    next_visit = sm.find_subject_visit_next_week(f'Dupi itch {subject_id} {subject_initials}')

    msg_blocks = []
    # Greeting
    # Figure out if we are addressing the proxy or subject
    # Haven't implemented both yet -- just address to subject for now
    if who_addressed == "Proxy":
        subject_address = Utils.get_clean_df_value(subject_data['Proxy address'])
    else:
        subject_address = Utils.get_clean_df_value(subject_data['Subject address'])

    msg_blocks.append(
        f"Hi {subject_address}! You are currently on week {subject_week} of the study. Here is your weekly reminder "
        f"for study tasks:")

    # Part A/B only
    # I suspect subject_week will be somewhat unreliable, but we will see
    if subject_week < 16:
        msg_blocks.append("Wear the sensor for at least 2 nights per week** Fri and Sat night are recommended.")
        msg_blocks.append("Fill out the blue diary everyday.")

    # All parts have surveys
    msg_blocks.append(f"Please fill out this survey: {link1}")
    if who_addressed == "Proxy" and subject_age >= 8:
        msg_blocks.append(f"Please have {subject_name} fill out this survey: {link2}")

    if next_visit is not None:
        if next_visit.visit_type is not None:
            msg_blocks.append(f"Your next visit is this upcoming week on {next_visit.nice_date} at {next_visit.nice_time} ({next_visit.visit_type})")
        else:
            msg_blocks.append(f"Your next visit is this upcoming week on {next_visit.nice_date} at {next_visit.nice_time}")

        if sm.need_pics(next_visit.week):
            msg_blocks.append("Please send pictures prior to your appointment.")

    # Find when their next dupi dose is
    next_dupi = sm.find_subject_visit_next_week(f'Dupi itch {subject_id} {subject_initials}', 'admin')
    if next_dupi is not None:
        # If the dupi shot is next week, the current week might be different from the dupi admin week
        dupi_week = sm.calculate_study_week(subject_enrollment_date, next_dupi.datetime, week_extensions)
        dupi_link = rc.get_survey_link(sdf, subject_id, dupi_week, who_addressed, 'dupi_survey')
        msg_blocks.append(f"Next dupilumab injection is due on {next_dupi.nice_date} ({next_dupi.day_of_week}).")
        msg_blocks.append(f"Please fill out this form after the injection: {dupi_link}")

    # To-do list reminders

    # Thank you block
    msg_blocks.append("")
    msg_blocks.append("Please reach out with any questions. Thank you!!")
    msg_blocks.append("-Brian")

    # Transform into safe string
    msg = format_list_with_numbers(msg_blocks)
    print(Utils.unsafe_string(msg))
    return msg
