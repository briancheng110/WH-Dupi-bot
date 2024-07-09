import Message
import Voice
import Subject_Management as sm
import Utils
import os
import csv
import pandas as pd
import Google_services as gs

work_queue_file = "Secrets/Work queue.csv"
completed_work_file = "Secrets/Completed work.csv"


class ToDoItem:
    def __init__(self, subject_id, subject_initials, date, msg):
        self.subject_id = subject_id
        self.subject_initials = subject_initials
        self.date = date
        self.msg = msg

    def __repr__(self):
        return f"ToDoItem(subject_id={self.subject_id}, subject_initials={self.subject_initials}, date={self.date}, msg={self.msg})"


def load_existing_entries(file_path):
    """ Load existing entries from a CSV file into a set for quick lookup. """
    existing_entries = set()
    try:
        with open(file_path, mode='r', newline='', encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    entry = tuple(row)
                    existing_entries.add(entry)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error while loading entries: {e}")
    return existing_entries


def add_wq(date, time, contact, msg):
    text_date = date.strftime("%m/%d/%Y")
    new_entry = (text_date, time, contact, msg)  # Format the new entry as a tuple

    # Load existing entries from the file
    existing_entries = load_existing_entries(work_queue_file)

    # Check if the new entry exists in the set of loaded entries
    if new_entry in existing_entries:
        print("Entry already exists, not adding to file.")
    else:
        # Append the new entry to the file if it's not a duplicate
        try:
            with open(work_queue_file, "a", encoding="utf-8") as file:
                file.write(f"{text_date},{time},{contact},{msg}\n")
        except Exception as e:
            print(f"Error while writing to the file: {e}")


def add_weekly_nag(sdf):
    next_friday = Utils.next_friday_date()
    for index, row in sdf.iterrows():
        subject = row['Subject']
        contact_person = row['Contact point']
        contact_method = row['Contact method']
        proxy_phone = row['Proxy phone']
        proxy_email = row['Proxy email']
        subject_phone = row['Subject phone']
        subject_email = row['Subject email']
        initials = row['Initials']
        skip = row['SkipWeekly']

        if skip == 'X':
            continue

        if contact_person == 'Both':
            msg = Message.build_message(sdf, subject, 'Proxy', next_friday)
            add_wq(next_friday, '21:00', proxy_phone, msg)

            msg = Message.build_message(sdf, subject, 'Subject', next_friday)
            add_wq(next_friday, '21:00', subject_phone, msg)
        else:
            if contact_person == 'Proxy':
                phone = proxy_phone
                email = proxy_email
            if contact_person == 'Subject':
                phone = subject_phone
                email = subject_email

            msg = Message.build_message(sdf, subject, contact_person, next_friday)
            add_wq(next_friday, '21:00', phone, msg)


def add_dupi_reminder(sdf):
    cal = gs.get_cal_service()
    calendar_id = "avcqb9cjn6etq0ftno6mrs82ag@group.calendar.google.com"
    dupi_admins = gs.find_dupi_events(cal, calendar_id, 6, 1, 'dupi')

    for event in dupi_admins:
        subj_data = sm.filter_by_id(sdf, event.subject_id)
        contact_person = Utils.get_clean_df_value(subj_data['Contact point'])
        proxy_phone = Utils.get_clean_df_value(subj_data['Proxy phone'])
        proxy_email = Utils.get_clean_df_value(subj_data['Proxy email'])
        subject_phone = Utils.get_clean_df_value(subj_data['Subject phone'])
        subject_email = Utils.get_clean_df_value(subj_data['Subject email'])
        skip = Utils.get_clean_df_value(subj_data['SkipDupi'])

        if skip == 'X':
            continue

        if contact_person == 'Both':
            msg = Message.build_dupi_message(sdf, event.subject_id, 'Proxy')
            add_wq(event.datetime, '21:00', proxy_phone, msg)

            msg = Message.build_dupi_message(sdf, event.subject_id, 'Subject')
            add_wq(event.datetime, '21:00', subject_phone, msg)
        else:
            if contact_person == 'Proxy':
                phone = proxy_phone
                email = proxy_email
            if contact_person == 'Subject':
                phone = subject_phone
                email = subject_email

            msg = Message.build_dupi_message(sdf, event.subject_id, contact_person)
            add_wq(event.datetime, '21:00', phone, msg)


def run_wq():
    driver = Voice.start_driver()
    wq = Utils.load_csv(work_queue_file)

    # Create an empty DataFrame for completed tasks
    completed_tasks = pd.DataFrame(columns=wq.columns)

    # Loop through each row in the DataFrame
    for index, row in wq.iterrows():
        # Extract message, date, contact
        msg = row['message']
        date = row['date']
        contact = row['contact']

        # Check if the message is due to be sent today
        if Utils.is_today(date):
            Utils.log(f"Due date: {date}, Message: {msg[:20]}... Action: GV send")
            Voice.send_gv_message(driver, contact, msg)

            # Add to completed tasks
            completed_tasks = pd.concat([completed_tasks, pd.DataFrame([row])], ignore_index=True)

            # Drop from work queue
            wq.drop(index, inplace=True)
        else:
            Utils.log(f"Due date: {date}, Message: {msg[:20]}... Action: not due today")

    # Save the updated DataFrame back to the CSV
    wq.to_csv(work_queue_file, index=False)

    # Append completed tasks to the completed work file
    # Check if the completed file exists and write appropriately
    try:
        if os.path.exists(completed_work_file):
            completed_tasks.to_csv(completed_work_file, mode='a', header=False, index=False)
        else:
            completed_tasks.to_csv(completed_work_file, index=False)
    except Exception as e:
        print(f"Error while writing to the completed file: {e}")

    Utils.log("Work queue updated and completed tasks moved.")


def collect_todo(sdf):
    pass
    
