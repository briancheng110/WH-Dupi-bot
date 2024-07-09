from seleniumbase import Driver
from selenium.webdriver.common.keys import Keys
import time
import random
import os

import Utils

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

msg_box = ('#messaging-view > div > md-content > gv-thread-details > div > div.gvThreadDetails-messageEntryContainer > '
           'gv-message-entry-ng2 > div > div > div.message-input-container > textarea')
newline = Keys.SHIFT + Keys.ENTER


def start_driver():
    data_dir = Utils.get_abs_path(script_dir, r'Secrets\selenium')

    # Output the chosen directory
    print(f"Using data directory: {data_dir}")
    
    driver = Driver(uc=True, headless=False, user_data_dir=data_dir)
    return driver


def send_gv_message(driver, phone_number, msg):
    # Take msg variable and replace ** with comma
    # Split new string on ;;, which is newline
    # Loop through list of strings stored into the var msg_list 
    # Execute driver.send_keys(msg_box, msg_list) for each item followed by driver.send_keys(msg_box, newline)
    msg_list = msg.replace('**', ',').split(';;')
   
    driver.uc_open_with_reconnect('https://voice.google.com/u/0/messages', 10)
    driver.uc_click("#messaging-view > div > md-content > div > div > div", reconnect_time=random.randint(5, 15))

    # Temporarily not using phone_number
    driver.type('#mat-mdc-chip-list-input-0', phone_number)
    driver.uc_click('#send_to_button-0', reconnect_time=2)
    
    # Loop through each message in the list and send it
    for line in msg_list:
        driver.send_keys(msg_box, line)   # Type a line
        driver.send_keys(msg_box, newline)  # Type a newline
    time.sleep(10)
    #driver.send_keys(msg_box, '\n') # send the message
    driver.uc_click('#messaging-view > div > md-content > gv-thread-details > div > '
                    'div.gvThreadDetails-messageEntryContainer > gv-message-entry-ng2 > div > div > div:nth-child(4) '
                    '> button > mat-icon')
