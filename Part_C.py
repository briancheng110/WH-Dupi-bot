import pandas as pd
import requests
subject_data = {
    'token': '0935374FD71B45F380F6877EBBFED84D',
    'content': 'record',
    'action': 'export',
    'format': 'json',
    'type': 'flat',
    'csvDelimiter': '',
    'records[0]': '12',
    'fields[0]': 'record_id',
    'fields[1]': 'nrs_worst_itch',
    'rawOrLabel': 'raw',
    'rawOrLabelHeaders': 'raw',
    'exportCheckboxLabel': 'false',
    'exportSurveyFields': 'false',
    'exportDataAccessGroups': 'false',
    'returnFormat': 'json'
}

proxy_data = {
    'token': '0935374FD71B45F380F6877EBBFED84D',
    'content': 'record',
    'action': 'export',
    'format': 'json',
    'type': 'flat',
    'csvDelimiter': '',
    'records[0]': '12',
    'fields[0]': 'record_id',
    'fields[1]': 'nrs_worst_itch_proxy',
    'rawOrLabel': 'raw',
    'rawOrLabelHeaders': 'raw',
    'exportCheckboxLabel': 'false',
    'exportSurveyFields': 'false',
    'exportDataAccessGroups': 'false',
    'returnFormat': 'json'
}

subject_part_A_events = [
    "part_a_screenbasel_arm_3",
    "diary_w7_arm_3",
    "visit_w6_virtual_arm_3",
    "diary_w5_arm_3",
    "visit_w4_clinic_arm_3",
    "diary_w3_arm_3",
    "visit_w2_virtual_arm_3",
    "diary_w1_arm_3",
    "part_a_extra_weekl_arm_3"
]

subject_part_B_events = [
    "diary_w9_arm_3",
    "visit_w10_virtual_arm_3",
    "diary_w11_arm_3",
    "visit_w12_clinic_arm_3",
    "diary_w13_arm_3",
    "visit_w14_virtual_arm_3",
    "diary_w15_arm_3",
    "visit_w16_clinic_arm_3",
    "part_b_extra_weekl_arm_3"
]

proxy_part_A_events = [
    "part_a_screenbasel_arm_2",
    "diary_w7_arm_2",
    "visit_w6_virtual_arm_2",
    "diary_w5_arm_2",
    "visit_w4_clinic_arm_2",
    "diary_w3_arm_2",
    "visit_w2_virtual_arm_2",
    "diary_w1_arm_2",
    "part_a_extra_weekl_arm_2"
]

proxy_part_B_events = [
    "diary_w9_arm_2",
    "visit_w10_virtual_arm_2",
    "diary_w11_arm_2",
    "visit_w12_clinic_arm_2",
    "diary_w13_arm_2",
    "visit_w14_virtual_arm_2",
    "diary_w15_arm_2",
    "visit_w16_clinic_arm_2",
    "part_b_extra_weekl_arm_2"
]


subject_r = requests.post('https://redcap.nubic.northwestern.edu/redcap/api/',data=subject_data)
proxy_r = requests.post('https://redcap.nubic.northwestern.edu/redcap/api/',data=proxy_data)
#print('HTTP Status: ' + str(r.status_code))

pd.set_option('display.max_columns', None)
subject_df = pd.DataFrame(subject_r.json())
proxy_df = pd.DataFrame(proxy_r.json())

# Filter the DataFrame to only include rows where the 'redcap_event_name' is in 'events_to_keep'
subject_part_A_df = subject_df[subject_df['redcap_event_name'].isin(subject_part_A_events)]
subject_part_A_df['nrs_worst_itch'] = pd.to_numeric(subject_part_A_df['nrs_worst_itch'], errors='coerce')

subject_part_B_df = subject_df[subject_df['redcap_event_name'].isin(subject_part_B_events)]
subject_part_B_df['nrs_worst_itch'] = pd.to_numeric(subject_part_B_df['nrs_worst_itch'], errors='coerce')

proxy_part_A_df = proxy_df[proxy_df['redcap_event_name'].isin(proxy_part_A_events)]
proxy_part_A_df['nrs_worst_itch_proxy'] = pd.to_numeric(proxy_part_A_df['nrs_worst_itch_proxy'], errors='coerce')

proxy_part_B_df = proxy_df[proxy_df['redcap_event_name'].isin(proxy_part_B_events)]
proxy_part_B_df['nrs_worst_itch_proxy'] = pd.to_numeric(proxy_part_B_df['nrs_worst_itch_proxy'], errors='coerce')


# Output the average
subject_average_itch_a = subject_part_A_df['nrs_worst_itch'].mean()
print("Part A NRS Worst Itch:", subject_average_itch_a)

subject_average_itch_b = subject_part_B_df['nrs_worst_itch'].mean()
print("Part B NRS Worst Itch:", subject_average_itch_b)

proxy_average_itch_a = proxy_part_A_df['nrs_worst_itch_proxy'].mean()
print("Part A NRS Worst Itch:", proxy_average_itch_a)

proxy_average_itch_b = proxy_part_B_df['nrs_worst_itch_proxy'].mean()
print("Part B NRS Worst Itch:", proxy_average_itch_b)
