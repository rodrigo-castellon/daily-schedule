'''
page_fetch.py fetches special schedule info, compiling into a readable .JSON format. It then saves this JSON object as a file
and also uploads it to a GitHub repo and website through FTP
'''

import time
import unicodedata
import datetime
import calendar

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options

from secrets import *
import sys, os, io
import re, json, ftplib
from threading import Timer
from github import Github
from bcolors import bcolors
import numpy as np
import select, sys
import argparse
import datetime

timeout = 10

month_dict = {k: v for k,v in enumerate(calendar.month_abbr)}
inverse_month_dict = {v: k for k,v in enumerate(calendar.month_abbr)}

start_time = time.time()
global r
r = re.compile('[0-9]{1,2}:[0-9]{2}')

class TimeoutExpired(Exception):
    pass

def get_data(fname='schedules.json'):
    try:
        with open('schedules.json') as f:
            data = json.load(f)
    except:
        data = {}
    return data

def input_with_timeout(prompt, timeout):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    ready, _, _ = select.select([sys.stdin], [],[], timeout)
    if ready:
        return sys.stdin.readline().rstrip('\n') # expect stdin to be line-buffered
    raise TimeoutExpired

def get_time_indices(text_array):
    global r
    vmatch = np.vectorize(lambda x:bool(r.search(x)))
    return vmatch(text_array)

def extract_from_doc(text_array):
    global r
    text_array = [x.strip().replace('\u200b', '') for x in text_array]
    # we can use 'Period' as our anchor point, since it is always the first cell in the table
    text_array = text_array[text_array.index([x for x in text_array if 'period' in x.lower()][0]) + 3:]
    
    time_indices = get_time_indices(text_array)
    period_indices = np.where(~time_indices)[0]
    time_indices = np.where(time_indices)[0]

    schedule_times = {}
    assert(len(text_array) % 3 == 0)
    for i in range(int(len(text_array) / 3)):
        index = i*3
        period = text_array[index]
        # take out anything within parentheses
        matches = list(re.finditer("\(.*?\)", period)) # finds everything with parentheses
        print("MATCHES: {}".format(matches))
        valuable_matches = [match for match in matches if len(list(re.finditer('[0-9]{1,2}', match.group()))) == 0]
        print("VALUABLE MATCHES: {}".format(valuable_matches))
        period = period[:matches[0].span()[0]] + ''.join([match.group() for match in valuable_matches])
        begin = text_array[index+1]
        end = text_array[index+2]
        
        begin = r.findall(begin)[0] if r.search(begin) else begin
        end = r.findall(end)[0] if r.search(end) else end
        schedule_times[period] = [begin, end]

    return schedule_times

def fetch_special_schedule(calendar_event):
    ### CLICKING ON CALENDAR EVENT
    calendar_event.click()

    ### EXTRACT DATE
    print("extracting date...")
    possible_years = [str(i+2017) for i in range(100)]
    try:
        time_date = browser.find_elements_by_class_name("odd")
        time_date = [x.text for x in time_date]
        time_date = [x for x in time_date if 'Time' in x][0].split()[1:]
        time_date = ' '.join(time_date)
        print('extracted. time_date: {}'.format(time_date))
    except:
        print("No special schedule date found.")
        return

    ### EXTRACT NAME OF SPECIAL SCHEDULE
    print("extracting name of special schedule...")
    try:
        sched_title = browser.find_element_by_class_name("template-title").text
        print('extracted.')
    except:
        print("No special schedule title found.")

    ### CLICK ON "VIEW ITEM" BUTTON
    print("clicking on \"view item\" button...")
    try:
        view_item_button = browser.find_element_by_partial_link_text("View Item")
    except:
        print("Could not find 'View Item' button. Going back to calendar feed.")
        browser.execute_script("window.history.go(-1)")
        browser.execute_script("window.history.go(+1)")
        return
    view_item_button.click()
    print("clicked.")

    ### GOING TO GOOGLE DOCUMENT FOR SCHEDULE
    print("attempting to go to the google doc...")
    link_to_schedule_XPATH = '//*[@class="ext  sExtlink-processed"]'
    try:
        link_to_schedule = browser.find_element_by_xpath(link_to_schedule_XPATH)
    except:
        print("unable to find google doc.")
        try:
            user = input_with_timeout("[Enter] to go back to the calendar.\n>", 3)
        except TimeoutExpired:
            pass
        browser.execute_script("window.history.go(-1)")
        return
    browser.execute_script("document.getElementsByClassName('ext   sExtlink-processed')[0].setAttribute('target', '_self');")
    link_to_schedule.click()
    print("clicked.")

    time.sleep(3)

    ### CHECKING IF REDIRECT
    is_redirect = True if len(browser.find_elements_by_class_name("extlink-redirect")) >= 1 else False
    if is_redirect:
        print("Redirecting...")
        link = browser.find_elements_by_partial_link_text("http")[0]
        link.click()
        time.sleep(1)

    ### CHECK IF THE GOOGLE DOC NEEDS LOGIN CREDENTIALS TO ACCESS IT, THEN LOG IN IF NEEDED
    is_login_page = True if len(browser.find_elements_by_class_name("ck6P8")) >= 1 else False
    if is_login_page:
        print("this document requires login credentials. logging in...")
        elem = browser.find_element_by_name("identifier")
        elem.clear()
        print("entering email address...")
        try:
            elem.send_keys(gdocs_email)
        except:
            print("ERROR: you probably don't have 'gdocs_email' defined in secrets.py")
            exit(0)
        print("entered.")
        print("pressing [Enter]...")
        elem.send_keys(Keys.RETURN)
        time.sleep(2)
        print('pressed.')
        print("finding password box...")
        elem = browser.find_element_by_name("password")
        print("entering password...")
        elem.send_keys(gdocs_password)
        elem.send_keys(Keys.RETURN)
        print("logged in.")
        time.sleep(2)

    ### GETTING ALL CELLS
    print('getting all cells...')
    cells = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name('kix-cellrenderer'))
    print('done. found {} cells'.format(len(cells)))
    text_elements = []

    ### ITERATING THROUGH EACH CELL
    print('iterating through each cell...')
    for cell in cells:
        cell_text = ''
        for child in cell.find_elements_by_css_selector("*"):
            if not(child.text in cell_text):
                cell_text += child.text
        cell_text = cell_text.strip()
        text_elements += [cell_text]
    print("iterated.")

    ### EXTRACTING TIMES
    print('extracting times...')
    schedule_times = extract_from_doc(text_elements)
    print('extracted.')

    ### LOAD INTO THE JSON OBJECT
    sched_json = {time_date: {
        'title': sched_title,
        'url': browser.current_url,
        'date': int(time_date.split()[2][:-1]),
        'month_num': inverse_month_dict[time_date.split()[1]],
        'datetime': str(datetime.datetime.strptime(time_date, '%A, %b %d, %Y')),
        'schedule': schedule_times
    }}


    try:
        with open('schedules.json') as f:
            data = json.load(f)
    except:
        data = {}
    
    data.update(sched_json)
    with open("schedules.json", "w") as f:
        json.dump(data, f)

    if is_redirect:
        browser.execute_script("window.history.go(-1)")

    if is_login_page: # This is because we logged in. Thus we need to go back twice extra.
        browser.execute_script("window.history.go(-1)")
        browser.execute_script("window.history.go(-1)")
    print("going back...")
    browser.execute_script("window.history.go(-1)")
    browser.execute_script("window.history.go(-1)")

def ftp_upload(data):
    print("connecting to FTP server...")
    try:
        ftp = ftplib.FTP(ftp_address)
    except:
        print("ERROR: you probably don't have 'ftp_address' defined in secrets.py.")
        exit(0)
    print("logging in...")
    try:
        ftp.login(user=ftp_username,passwd=ftp_passwd)
    except:
        print("ERROR: 'ftp_username' or 'ftp_passwd' are probably not defined in secrets.py."
            "These are the username and password to get into your FTP server for your website.")
        exit(0)

    print("changing directory...")
    ftp.cwd('/dailyschedule.atwebpages.com/scripts')

    print("uploading schedules.json...")
    ftp.storbinary("STOR schedules.json", open("schedules.json","rb"))

    print("quitting FTP server...")
    ftp.quit()

def gh_upload(data):
    print("logging into GitHub...")
    try:
        g = Github(gh_username, gh_password)
    except:
        print("ERROR: you probably don't have 'gh_username' or 'gh_password' defined in secrets.py."
            "PyGithub is also used to host schedules.json")
        exit(0)
    print("searching for elearning repo...")
    for repo in g.get_user().get_repos():
        if repo.name == "elearning":
            print("found elearning repo")
            print("committing schedules.json...")
            file = repo.get_file_contents("/schedules.json")
            repo.update_file("/schedules.json", "this commit is an update", open("schedules.json","rb").read(), file.sha)
            print("finished!")

def main_process(upload_ftp=False, upload_gh=False):
    # Main fetch process begins here
    global browser
    browser = webdriver.Chrome(os.getcwd() + '/chromedriver')
    ### GO TO INITIAL WEBPAGE
    try:
        browser.get(webaddress)
    except:
        print("ERROR: you probably don't have 'webaddress' defined in secrets.py."
            "'webaddress' is 'http://elearning.pinecrest.edu' in this case.")
        exit(0)
    assert("Sign in" in browser.page_source)
    
    ### ENTER USERNAME
    print("logging in...")
    elem =  browser.find_element_by_name("username")
    elem.clear()
    try:
        elem.send_keys(username)
    except:
        print("ERROR: you probably don't have 'username' defined in secrets.py")
        exit(0)
    
    ### ENTER PASSWORD
    elem = browser.find_element_by_name("password")
    try:
        elem.send_keys(password)
    except:
        print("ERROR: you probably don't have 'password' defined in secrets.py")
        exit(0)
    
    ### PRESS "LOG IN"
    elem.send_keys(Keys.RETURN)

    ### FIND THE "CALENDAR" BUTTON
    first_result = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_partial_link_text('Calendar'))
    print("logged in.")
    print("clicking \"Calendar\" button...")
    button_to_calendar = browser.find_element_by_partial_link_text("Calendar")

    ### CLICK THE "CALENDAR" BUTTON
    button_to_calendar.send_keys(Keys.CONTROL + Keys.RETURN)
    print("clicked.")

    time.sleep(1.)

    ### BEGIN MAIN LOOP
    delta_month = 0
    while True:
        ### ASK FOR USER INPUT
        while True:
            ### GET AND PRINT OUT THE NAME OF THE MONTH IN TERMINAL
            month = browser.find_element_by_class_name("fc-header-title").text.split()[0]

            ### GET HOW MANY ARE ALREADY STORED IN "schedules.json"
            data = get_data()
            keys = list(data.keys())
            occurrences = len([x for x in keys if month[:3] in x])
            print(bcolors.BOLD + bcolors.HEADER + month + " (" + str(occurrences) + " already stored)" + bcolors.ENDC)
            user = input("Do you want to scan?\n"
                         "- [y]es\n"
                         "- move to [n]ext month\n"
                         "- move [b]ack to last month?\n"
                         "- all [d]one\n"
                         ">")
            if user in ['y', 'yes']:
                break
            elif user == 'n':
                delta_month += 1
                forwardback_buttons = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name("fc-button-content"))
                forwardback_buttons[1].click()
            elif user == 'b':
                delta_month -= 1
                forwardback_buttons = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name("fc-button-content"))
                forwardback_buttons[0].click()
            elif user in ['d', 'done']:
                break
        if user in ['d', 'done']:
            break
        
        ### BEGIN LOOP FOR A SINGLE MONTH
        ### GET A LIST OF ALL EVENTS
        print("getting a list of all events...")
        calendar_events = browser.find_elements_by_class_name("fc-event-title")
        print("found.")

        ### LOOP THROUGH EVENTS AND CHECK ONLY SPECIAL SCHEDULES
        print(bcolors.WARNING + "EVENTS:" + bcolors.ENDC)
        for i in range(len(calendar_events)):
            calendar_event = calendar_events[i]
            # This can an especially fragile part of the script. It only looks at
            # calendar events if it matches one of the strings in it
            matches = ["special schedule", "weekly show", "block schedule", "pctv"]
            if sum([x in calendar_event.text.lower() for x in matches]) > 0:
                data = get_data()
                is_present = False
                for key in data.keys():
                    if data[key]['title'] == calendar_event.text:
                        is_present = True
                        break
                bold_type = bcolors.OKGREEN if (is_present) else bcolors.BOLD + bcolors.OKGREEN
                print("{}- {}{}".format(bold_type, calendar_event.text, bcolors.ENDC))

                try:
                    user = input_with_timeout("Do you want to add this schedule?\n"
                             "- [y]es\n"
                             "- [n]o\n"
                             ">", 10)
                except TimeoutExpired:
                    user = 'y'
                if not(user in ['y', 'yes']):
                    continue
                fetch_special_schedule(calendar_event)
                ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name('fc-button-content'))
                time.sleep(0.5)
                ### GO BACK TO USER'S MONTH
                print("DELTA MONTH: {}".format(delta_month))
                match = ("Next", 1) if delta_month > 0 else ("Back", 0)
                for i in range(abs(delta_month)):
                    #print("BLOEUHLOEURLEODUROGEDURGDOELRDUO")
                    forwardback_buttons = ui.WebDriverWait(browser, 5).until(find)
                    time.sleep(0.1)
                    forwardback_buttons[match[1]].click()
                    time.sleep(0.1)
                print('getting a list of all events...')
                calendar_events = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name("fc-event-title"))
                print('found.')
            else:
                print("- {}".format(calendar_event.text))

    print("Success! {0}: {1} schedules; {2}: {3} schedules; Process took {4} seconds.".format(
            this_month,
            current_month_items,
            month_dict[(datetime.datetime.now().month+1) % 12],
            len(calendar_events),
            (time.time()-start_time)))

    with open('schedules.json') as f:
        data = json.load(f)

    if upload_ftp:
        ftp_upload(data)
    if upload_gh:
        gh_upload(data)

    return data

def find(browser):
    element = browser.find_elements_by_class_name("fc-button-content")
    if element:
        return element
    else:
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--upload", action='store_true', help="upload schedules.json to the FTP server and the github page")
    args = parser.parse_args()
    if args.upload:
        with open('schedules.json') as f:
          data = json.load(f)
        ftp_upload(data)
        gh_upload(data)
    else:
        data = main_process(upload_ftp=True, upload_gh=True)
