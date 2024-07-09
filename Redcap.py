import json
import Utils
import requests
import Subject_Management as sm
from rc_lookup import rc_lookup, dupi_rc_lookup
import pprint


def redcap_read_api_key(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        print("File not found or path is incorrect.")
    except IOError:
        print("Error reading the file.")


api_key_file = "Secrets/Redcap_API_token.txt"
# api_key_file = "Secrets\\Redcap_API_token_test.txt"
api_token = redcap_read_api_key(api_key_file)
api_url = 'https://redcap.nubic.northwestern.edu/redcap/api/'


def age_to_arm(age):
    if age < 18:
        return 1
    else:
        return 3


def gen_blank_record(record_id, event_name, form_name, repeat_instance):
    """
    Generate a blank record

    Parameters:
    - record_id: The ID of the record to import.
    - event_name: The event name associated with the record.
    - repeat_instrument: The name of the repeating instrument.
    - repeat_instance: The instance number of the repeating instrument.
    """
    # Data payload for the record import
    data = [{
        'record_id': int(record_id),
        'redcap_event_name': event_name,
        'redcap_repeat_instrument': form_name,
        'redcap_repeat_instance': repeat_instance
    }]

    # Setup the request payload
    post_data = {
        'token': api_token,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'overwriteBehavior': 'overwrite',
        'data': json.dumps(data),
        'returnContent': 'count',
        'returnFormat': 'json'
    }

    # Make the POST request to the REDCap API
    response = requests.post(api_url, data=post_data)
    if response.status_code == 200:
        # print("Success: Record imported successfully.")
        return response.json()
    else:
        print("Error: Failed to import record.", response.status_code, response.text)
        return None


def api_survey_link_repeat(record_id, event_name, form_name, instance):
    """ Generate a survey link for a new instance """
    payload = {
        'token': api_token,
        'content': 'surveyLink',
        'format': 'json',
        'record': int(record_id),
        'event': event_name,
        'instrument': form_name,
        'repeat_instance': instance
    }
    response = requests.post(api_url, data=payload)
    if response.status_code == 200:
        survey_link = response.text
        return survey_link
    else:
        print('Failed to generate survey link:', response.status_code, response.text)
        return None


def api_survey_link_single(record_id, event_name, form_name):
    """ Generate a survey link for a new instance """
    payload = {
        'token': api_token,
        'content': 'surveyLink',
        'format': 'json',
        'record': int(record_id),
        'event': event_name,
        'instrument': form_name
    }
    response = requests.post(api_url, data=payload)
    if response.status_code == 200:
        survey_link = response.text
        return survey_link
    else:
        print('Failed to generate survey link:', response.status_code, response.text)
        return None


def redcap_lookup(week, arm, is_proxy, is_dupi):
    arm_key = str(arm)
    week_key = str(week)
    if is_dupi:
        lookup_table = dupi_rc_lookup
    else:
        lookup_table = rc_lookup

    try:
        if is_proxy == True:
            proxy_key = 'Proxy'
            return lookup_table[proxy_key][week_key]  # no arm key for proxies, this is always 2
        else:
            proxy_key = 'Subject'
            return lookup_table[proxy_key][arm_key][week_key]
    except KeyError as e:
        print('Bad key')
        return 'None'


def is_form_repeating(event_name, form_name):
    post_data = {
        'token': api_token,
        'content': 'repeatingFormsEvents',
        'format': 'json',
        'returnFormat': 'json'
    }
    r = requests.post(api_url, data=post_data)

    # Parse the JSON string into a dictionary
    data = r.json()

    for item in data:
        if item['event_name'] == event_name and item['form_name'] == form_name:
            return True
    return False


def download_record(record_id, event_name, form_name):
    post_data = {
        'token': api_token,
        'content': 'record',
        'action': 'export',
        'format': 'json',
        'type': 'flat',
        'csvDelimiter': '',
        'records[0]': record_id,
        'fields[0]': 'record_id',
        'forms[0]': form_name,
        'events[0]': event_name,
        'rawOrLabel': 'raw',
        'rawOrLabelHeaders': 'raw',
        'exportCheckboxLabel': 'false',
        'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json'
    }
    # print(post_data)
    r = requests.post(api_url, data=post_data)
    # print('HTTP Status: ' + str(r.status_code))

    data = r.json()
    return data


def check_survey_status():
    pass


def get_survey_link(sdf, subject_id, week, who_addressed, form='weekly_survey'):
    subject_data = sm.filter_by_id(sdf, subject_id)

    if form == 'weekly_survey':
        if who_addressed == 'Proxy':
            record_id = Utils.get_clean_df_value(subject_data['Proxy record ID'])
            form_name = 'weekly_surveys_proxy'
            event_name = redcap_lookup(week, 2, True, False)
        else:
            record_id = Utils.get_clean_df_value(subject_data['Subject record ID'])
            age = Utils.get_clean_df_value(subject_data['Age'])
            arm = age_to_arm(age)
            form_name = 'weekly_surveys_child_8yo'
            event_name = redcap_lookup(week, arm, False, False)
    else:
        form_name = 'dupilumab_administration_diary'
        age = Utils.get_clean_df_value(subject_data['Age'])
        if age < 18:
            record_id = Utils.get_clean_df_value(subject_data['Proxy record ID'])
            event_name = redcap_lookup(week, 2, True, True)
        else:
            record_id = Utils.get_clean_df_value(subject_data['Subject record ID'])
            event_name = redcap_lookup(week, 3, False, True)

    #print(event_name)
    if is_form_repeating(event_name, form_name):
        record = download_record(record_id, event_name, form_name)
        # print(record)

        # For the first instance, Redcap can either return:
        # - blank (meaning zero instances)
        # - full response with redcap_repeat_instance = '' (ghost instance)
        if len(record) == 0:
            max_instance = 0
        else:
            max_instance = record[-1]['redcap_repeat_instance']

            # Ghost instance handler
            try:
                if len(max_instance) == 0:
                    max_instance = 0
            except TypeError:
                pass
        # print(max_instance)

        # generate a new blank record
        new_instance = max_instance + 1
        gen_blank_record(record_id, event_name, form_name, new_instance)
        link = api_survey_link_repeat(record_id, event_name, form_name, new_instance)

    else:
        link = api_survey_link_single(record_id, event_name, form_name)

    Utils.log(
        f'Link generated - SubjectID: {subject_id}\tRecordID: {record_id}\tForm: {form_name}\tWeek: {week}\tAddress: {who_addressed}\tLink: {link}')
    return link
