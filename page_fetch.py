""" Fetches special schedule info across arbitrary number of months, compiles these into a readable JSON format,
saves them onto a file, and uploads to a GitHub repo and website through FTP.
"""

import time
import unicodedata
import datetime
import calendar

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, InvalidElementStateException
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options

from secrets import *
import sys
import os
import io
import re
import json
import ftplib
from threading import Timer
from github import Github
from bcolors import bcolors
import numpy as np
import select, sys
import argparse
import datetime
import operator

timeout = 10

month_dict = {k: v for k,v in enumerate(calendar.month_abbr)}
inverse_month_dict = {v: k for k,v in enumerate(calendar.month_abbr)}

class TimeoutExpired(Exception):
    pass

def get_data(fname='schedules.json'):
    """ Get the dictionary from the .json file. """
    try:
        with open('schedules.json') as f:
            data = json.load(f)
    except:
        data = {}
    return data

def input_with_timeout(prompt, timeout):
    """ Prompt the user to input text but with a timeout. """

    sys.stdout.write(prompt)
    sys.stdout.flush()
    ready, _, _ = select.select([sys.stdin], [],[], timeout)
    if ready:
        return sys.stdin.readline().rstrip('\n') # expect stdin to be line-buffered
    raise TimeoutExpired

def extract_from_doc(text_array):
    """ Convert the list of pieces of text within cells in the Google Doc into a usable
    dictionary format and return it.
    """

    r = re.compile('[0-9]{1,2}:[0-9]{2}')  # Matches clock times

    text_array = [re.sub(r'[^\x00-\x7F]|[\n,\r,\t,\v]+', '', x) for x in text_array]
    text_array = text_array[3:]

    schedule_times = {}
    assert(len(text_array) % 3 == 0)
    for period, start, stop in zip(*[text_array[x:][::3] for x in range(3)]):
        period = re.sub('\([^(\(,\))]*\d+[^(\(,\))]*\)', '', period).strip()
        start = r.findall(start)[0] if r.search(start) else start
        stop = r.findall(stop)[0] if r.search(stop) else stop
        schedule_times[period] = [start, stop]

    return schedule_times

def fetch_special_schedule(calendar_event):
    """ Fetch a single special schedule on the calendar page.  """

    ### CLICKING ON CALENDAR EVENT
    calendar_event.click()

    ### EXTRACT DATE
    print("extracting date...")
    possible_years = [str(i+2017) for i in range(100)]
    try:
        time_date = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name("odd"))
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
        sched_title = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_class_name("template-title").text)
        print('extracted.')
    except:
        print("No special schedule title found.")

    ### CLICK ON "VIEW ITEM" BUTTON
    print("clicking on \"view item\" button...")
    try:
        view_item_button = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_partial_link_text("View Item"))
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
    except NoSuchElementException:
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
        link = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_partial_link_text("http")[0])
        link.click()
        time.sleep(1)

    ### CHECK IF THE GOOGLE DOC NEEDS LOGIN CREDENTIALS TO ACCESS IT, THEN LOG IN IF NEEDED
    is_login_page = True if len(browser.find_elements_by_class_name("ck6P8")) >= 1 else False
    if is_login_page:
        print("this document requires login credentials. logging in...")
        elem = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_name("identifier"))
        elem.clear()
        print("entering email address...")
        try:
            elem.send_keys(gdocs_email)
        except NameError:
            print("ERROR: you probably don't have 'gdocs_email' defined in secrets.py")
            exit(0)
        print("entered.")
        print("pressing [Enter]...")
        elem.send_keys(Keys.RETURN)
        time.sleep(2)
        print('pressed.')
        print("finding password box...")
        elem = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_name('password'))
        print("entering password...")
        while True:
            try:
                elem.send_keys(gdocs_password)
                break
            except InvalidElementStateException:
                print("USER! CLICK THERE!")
                time.sleep(1)
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
    try:
        date_time = str(datetime.datetime.strptime(time_date, '%A, %b %d, %Y'))
    except ValueError as v:
        if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
            altered = time_date[:-(len(v.args[0]) - 26)]
            date_time = str(datetime.datetime.strptime(altered, '%A, %b %d, %Y'))
        else:
            raise
    sched_json = {
        date_time: {
            'title': sched_title,
            'url': browser.current_url,
            'time_date': time_date,
            'schedule': schedule_times
        }
    }


    data = get_data()
    
    data.update(sched_json)
    with open("schedules.json", "w") as f:
        json.dump(data, f)

    print("going back...")
    while True:
        browser.execute_script("window.history.go(-1)")
        try:
            browser.find_element_by_xpath('//*[@id="fcalendar"]/table/tbody/tr/td[2]/span')
        except NoSuchElementException:
            continue
        else:
            break

def ftp_upload(data):
    """ Upload the data (encoded as a dictionary) to the FTP server. """

    print("connecting to FTP server...")
    try:
        ftp = ftplib.FTP(ftp_address)
    except NameError:
        print("ERROR: you probably don't have 'ftp_address' defined in secrets.py.")
        exit(0)
    print("logging in...")
    try:
        ftp.login(user=ftp_username,passwd=ftp_passwd)
    except NameError:
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
    """ Upload the data (encoded as a dictionary) to GitHub. """
    print("logging into GitHub...")
    try:
        g = Github(gh_username, gh_password)
    except NameError:
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
    """ Run the main user-directed schedule fetching process. """

    global browser
    browser = webdriver.Chrome(os.getcwd() + '/chromedriver')
    ### GO TO INITIAL WEBPAGE
    try:
        browser.get(webaddress)
    except NameError:
        print("ERROR: you probably don't have 'webaddress' defined in secrets.py."
            "'webaddress' is 'http://elearning.pinecrest.edu' in this case.")
        exit(0)
    assert("Sign in" in browser.page_source)
    
    ### ENTER USERNAME
    print("logging in...")
    elem =  ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_name("username"))
    elem.clear()
    try:
        elem.send_keys(username)
    except NameError:
        print("ERROR: you probably don't have 'username' defined in secrets.py")
        exit(0)
    
    ### ENTER PASSWORD
    elem = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_name("password"))
    try:
        elem.send_keys(password)
    except NameError:
        print("ERROR: you probably don't have 'password' defined in secrets.py")
        exit(0)
    
    ### PRESS "LOG IN"
    elem.send_keys(Keys.RETURN)

    ### FIND THE "CALENDAR" BUTTON
    first_result = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_partial_link_text('Calendar'))
    print("logged in.")
    print("clicking \"Calendar\" button...")
    button_to_calendar = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_partial_link_text("Calendar"))

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
            month = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_class_name("fc-header-title").text.split()[0])

            ### GET HOW MANY ARE ALREADY STORED IN "schedules.json"
            data = get_data()
            occurrences = len([0 for key,item in data.items() if month[:3] in item['time_date']])
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
        calendar_events = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name("fc-event-title"))
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
                for key, item in data.items():
                    if item['time_date'] == calendar_event.text:
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
                ui.WebDriverWait(browser, 15).until(find_button)
                time.sleep(0.5)
                ### GO BACK TO USER'S MONTH
                print("DELTA MONTH: {}".format(delta_month))
                match = ("Next", 1) if delta_month > 0 else ("Back", 0)
                for i in range(abs(delta_month)):
                    #print("BLOEUHLOEURLEODUROGEDURGDOELRDUO")
                    forwardback_buttons = ui.WebDriverWait(browser, 5).until(find_button)
                    time.sleep(0.1)
                    forwardback_buttons[match[1]].click()
                    time.sleep(0.1)
                print('getting a list of all events...')
                calendar_events = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_class_name("fc-event-title"))
                print('found.')
            else:
                print("- {}".format(calendar_event.text))

    data = get_data()

    if upload_ftp:
        ftp_upload(data)
    if upload_gh:
        gh_upload(data)

    return data

def find_redirect(browser):
    """ Find an element that will redirect to another page. """

    element = browser.find_elements_by_class_name("extlink-redirect")
    if element:
        return element
    else:
        return False

def find_button(browser):
    """ Find an button element. """

    element = browser.find_elements_by_class_name("fc-button-content")
    if element:
        return element
    else:
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--upload", action='store_true', help="upload schedules.json to the FTP server and the github page")
    parser.add_argument("--test", action='store_true', help="test the 'extract_from_doc' function on 'extra.py' text arrays")
    parser.add_argument("-n", help="number of tests", type=int)
    args = parser.parse_args()
    if args.upload:
        with open('schedules.json') as f:
          data = json.load(f)
        data = data.sort(key=operator.attrgetter('count'))
        ftp_upload(data)
        gh_upload(data)
    elif args.test:
        from extra import text_arrays
        for i, text_array in enumerate(text_arrays):
            if i == args.n:
                break
            print("OUTPUT:\n{}".format(extract_from_doc(text_array)))
    else:
        data = main_process(upload_ftp=True, upload_gh=True)
