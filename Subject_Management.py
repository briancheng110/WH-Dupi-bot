import datetime
import pandas as pd
from openpyxl.reader.excel import load_workbook
import Google_services as gs
import math
from datetime import timedelta
from zoneinfo import ZoneInfo
import pytz
import os
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


class SubjectData:
    def __init__(self, dt, subject_id, subject_initials, week, study_name, days_until_visit, visit_type, event_id,
                 description):
        pass

    def __repr__(self):
        pass


def load_subjects():
    # Correct file path
    subjects_file = "Secrets/Dupi itch subjects.xlsx"

    # Open the workbook in read-only mode
    workbook = load_workbook(subjects_file, read_only=True)

    # Read the 'Subjects' sheet into a DataFrame
    with pd.ExcelFile(subjects_file, engine='openpyxl') as excel_file:
        sdf = pd.read_excel(excel_file, sheet_name='Subjects')

    def clean_value(x):
        control_chars = '[\u202A\u202C]'
        if isinstance(x, str):
            return re.sub(control_chars, '', x)
        return x

    sdf_cleaned = sdf.applymap(clean_value)

    return sdf_cleaned


def find_subjects_due_today(df):
    """
    Finds subjects in the DataFrame whose 'Next item due' matches today's date.
    
    Parameters:
    - df: pandas DataFrame, expected to contain a 'Next item due' column with dates.
    
    Returns:
    - A pandas DataFrame containing the rows where 'Next item due' is today's date.
    """
    # Ensure the 'Next item due' column is parsed as datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df['next_item_due']):
        df['Next item due'] = pd.to_datetime(df['next_item_due'], errors='coerce')

    # Get today's date
    today = datetime.today().date()
    tomorrow = (datetime.today() + datetime.timedelta(days=1)).date()

    # Filter rows where 'Next item due' is today's date
    matches_today = df[df['next_item_due'].dt.date == today]

    return matches_today


def filter_by_id(sdf, subject_id):
    filtered_df = sdf[sdf['Subject'] == int(subject_id)]
    return filtered_df


def filter_by_initials(sdf, subject_initials):
    filtered_df = sdf[sdf['Initials'] == subject_initials]
    return filtered_df


def find_subject_visit_next_week(subj_id_str, visit='visit'):
    service = gs.get_cal_service()
    calendar_id = "avcqb9cjn6etq0ftno6mrs82ag@group.calendar.google.com"

    # Calculate start and end dates for next week
    # today = datetime.datetime.now()
    # Yes this is a manual hack and I am disgusted
    manual_offset = 0
    today = datetime.datetime.now() + datetime.timedelta(days=1 + manual_offset)
    days_until_next_saturday = (5 - today.weekday() + 7) % 7

    # If today is Saturday, days_until_next_saturday will be 0, so add 7 days
    if days_until_next_saturday == 0:
        days_until_next_saturday = 7

    # Calculate next week's Saturday midnight
    start_dt = (today + timedelta(days=days_until_next_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
    days_until_next_friday = days_until_next_saturday + 6

    # Calculate next week's Friday 11:59:59 PM
    end_dt = (today + timedelta(days=days_until_next_friday)).replace(hour=23, minute=59, second=59, microsecond=0)
    local_timezone = pytz.timezone("America/Chicago")  # Replace with your local time zone

    # Localize the datetime objects
    start_dt_localized = local_timezone.localize(start_dt)
    end_dt_localized = local_timezone.localize(end_dt)

    # Convert to ISO 8601 format including the time zone offset for Google Calendar API call
    start_dt_iso = start_dt_localized.isoformat()
    end_dt_iso = end_dt_localized.isoformat()

    try:
        if visit == 'visit':
            next_visit = gs.find_next_upcoming_visit(service, calendar_id, subj_id_str, start_dt_iso, end_dt_iso)
            return next_visit
        else:
            next_admin = gs.find_next_upcoming_visit(service, calendar_id, subj_id_str, start_dt_iso, end_dt_iso,
                                                     'admin')
            return next_admin
    except TypeError as e:
        # Handle the TypeError here
        print(f"An error occurred: {e}")

        # Optionally, return None or perform other error handling actions
        return None


def need_pics(subject_week):
    picture_weeks = [-8, 0, 4, 8, 12, 16, 36, 52]
    if subject_week in picture_weeks:
        return True
    else:
        return False


def calculate_study_week(enrollment_date, target_date, week_extensions):
    """
    Calculates the study week number for a subject based on their enrollment date
    and the target date. Each new week starts on Sunday.
    """
    chicago_zone = ZoneInfo("America/Chicago")
    if enrollment_date.tzinfo is None or enrollment_date.tzinfo.utcoffset(enrollment_date) is None:
        enrollment_date = enrollment_date.replace(tzinfo=chicago_zone)

    if target_date.tzinfo is None or target_date.tzinfo.utcoffset(target_date) is None:
        target_date = target_date.replace(tzinfo=chicago_zone)
    manual_offset = 0
    # Calculate the most recent Sunday for target_date and enrollment_date
    target_sunday = target_date - timedelta(days=(target_date.weekday() + 1) % 7)
    enrollment_sunday = enrollment_date - timedelta(days=(enrollment_date.weekday() + 1) % 7)

    # Calculate the number of weeks between the two Sundays
    weeks_diff = (target_sunday - enrollment_sunday).days // 7

    # Adjust the week number by subtracting 8 weeks and adding any week extensions
    current_week = weeks_diff - 8 - week_extensions + manual_offset

    return current_week


def next_dose_date(start_date, dosing_interval_weeks):
    """
    Calculates the next dose date for a medication based on the start date and the dosing interval in weeks.

    Args:
    start_date (datetime.date): The date when the medication was first taken.
    dosing_interval_weeks (int): The interval between doses in weeks.

    Returns:
    datetime.date: The next due date for the medication dose.
    """
    # Convert today's date to a datetime.date object
    today = datetime.date.today()

    # Calculate the interval in days
    dosing_interval_days = dosing_interval_weeks * 7

    # Calculate the number of days from the start date to today
    days_since_start = (today - start_date).days

    # Calculate the number of complete dosing intervals that have elapsed
    completed_intervals = math.ceil(days_since_start / dosing_interval_days)

    # Calculate the next dose date
    next_dose = start_date + datetime.timedelta(days=completed_intervals * dosing_interval_days)

    return next_dose
