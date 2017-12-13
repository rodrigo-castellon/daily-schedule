import time
import unicodedata
import datetime
import calendar

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui

from secrets import *
import sys, os, io
import re
import types
import json
import ftplib
from github import Github

month_dict = {k: v for k,v in enumerate(calendar.month_abbr)}
month_dict[13] = 'Jan' # Line 250 tries to print out month_dict[datetime.datetime.now().month+1], which is invalid when it's December
inverse_month_dict = {v: k for k,v in enumerate(calendar.month_abbr)}

start_time = time.time()

def find_indices(str, ch):
	indices = []
	for i, ltr in enumerate(str):
		if ltr == ch:
			indices.append(i)
	return indices

def fix_text_array(input_text_array):
	regex_query = r'1[0-2]:[0-5][0-9]|[0-9]:[0-5][0-9]'
	text_array = input_text_array
	i = 0
	while True:
		if i >= len(text_array)/3:
			break
		if (not re.match(regex_query, text_array[i*3+1])):
			del text_array[i*3+1]
			i = 0
			continue
		if (not re.match(regex_query, text_array[i*3+2])):
			del text_array[i*3+2]
			i = 0
			continue
		i += 1
	if len(text_array) % 3 != 0:
		raise ValueError("Expected length of 'text_array' to be divisible by 3. Length is {}\n".format(len(text_array)))
	else:
		return text_array

def extract_period_info(text_array):
	for i in range(len(text_array)):
		text_array[i] = text_array[i].encode('utf-8')
	i = 0
	while i < len(text_array):
		text = text_array[i]
		if len(text) == 0 or text.isspace():
			del text_array[i]
			continue
		if re.match(r'\(.*\)',text):
			del text_array[i]
			continue
		text_array[text_array.index(text)] = text.replace(" ","")
		i += 1
	i = 0
	while True:
		if text_array[i][0] == "8" or text_array[i][0] == "1":
			text_array = text_array[i:]
			break
		i += 1
	
	if text_array[0] == "8:05":
		del text_array[0]
	text_array = fix_text_array(text_array)

	schedule_times = {}
	for i in range(len(text_array)/3):
		schedule_times[text_array[i*3]] = (text_array[i*3+1], text_array[i*3+2])
	return schedule_times

def fetch_special_schedule(sched_index):
	calendar_events = browser.find_elements_by_class_name("fc-event-title")
	calendar_events_temp = []
	i = 0
	while i < len(calendar_events):
		if "Special Schedule" in calendar_events[i].text:
			calendar_events_temp.append(calendar_events[i])
		i += 1
	calendar_events = calendar_events_temp
	if len(calendar_events) == 0:
		print("No links found. Try again.")
		sys.exit()
	print("Fetching special schedule " + str(sched_index+1) + " of " + str(len(calendar_events)))


	calendar_events[sched_index].click()

	# adjust_to_click()

	# Extract the date
	possible_years = [str(i+2017) for i in range(100)]
	try:
		time_date = browser.find_elements_by_class_name("odd")
	except:
		print("No special schedule date found.")
	for i in range(len(time_date)):
		for j in range(len(possible_years)):
			if possible_years[j] in time_date[i].text:
				time_date = time_date[i]
				time_date = time_date.text[5:] # Original time_date may be "Time Wednesday, Nov 5, 2017"
				time_date = time_date.encode('utf-8')
				print("Date: " + time_date)
				break
		if type(time_date) != type([]):
			break

	# Extract the name of the special schedule
	try:
		sched_title = browser.find_element_by_class_name("template-title").text
	except:
		print("No special schedule title found.")

	try:
		view_item_button = browser.find_element_by_partial_link_text("View Item")
	except:
		print("Could not find 'View Item' button. Going back to calendar feed.")
		browser.execute_script("window.history.go(-1)")
		browser.execute_script("window.history.go(+1)")
		return
	view_item_button.click()

	link_to_schedule_XPATH = '//*[@class="ext  sExtlink-processed"]'

	link_to_schedule = browser.find_element_by_xpath(link_to_schedule_XPATH)
	browser.execute_script("document.getElementsByClassName('ext   sExtlink-processed')[0].setAttribute('target', '_self');")

	link_to_schedule.click()

	time.sleep(3)

	# Checking if this page needs login, then adjusting accordingly

	is_login_page = True if len(browser.find_elements_by_class_name("FgbZLd")) >= 1 else False

	if is_login_page:
		print("Waiting for login...")
		elem = browser.find_element_by_name("identifier")
		elem.clear()
		try:
			elem.send_keys(gdocs_email)
		except:
			print("ERROR: you probably don't have 'gdocs_email' defined in secrets.py")
			exit(0)
		elem.send_keys(Keys.RETURN)
		time.sleep(2)
		elem = browser.find_element_by_name("password")
		try:
			elem.send_keys(gdocs_password)
		except:
			print("ERROR: you probably don't have 'gdocs_password' defined in secrets.py")
			exit(0)
		elem.send_keys(Keys.RETURN)
		time.sleep(2)

	schedule_times = [text.text for text in browser.find_elements_by_class_name("kix-wordhtmlgenerator-word-node")]
	schedule_times = extract_period_info(schedule_times)

	sched_json = {time_date: {
		'title': sched_title,
		'url': browser.current_url,
		'schedule': schedule_times,
		'date': int(filter(str.isdigit,time_date)[:-4]),
		'month_num': inverse_month_dict[time_date[find_indices(time_date, ',')[0]+2:find_indices(time_date, ',')[0]+5]]
	}}


	with open('schedules.json') as f:
		data = json.load(f)

	data.update(sched_json)
	with open("schedules.json", "w") as f:
		json.dump(data, f)

	if is_login_page: # This is because we logged in. Thus we need to go back twice extra.
		browser.execute_script("window.history.go(-1)")
		browser.execute_script("window.history.go(-1)")
	print("going back...")
	browser.execute_script("window.history.go(-1)")
	browser.execute_script("window.history.go(-1)")

# Main fetch process begins here
browser = webdriver.Chrome(os.getcwd())
try:
	browser.get(webaddress)
except:
	print("ERROR: you probably don't have 'webaddress' defined in secrets.py. 'webaddress' is 'http://elearning.pinecrest.edu' in this case.")
	exit(0)
assert "Sign in" in  browser.page_source
print("logging in...")
elem =  browser.find_element_by_name("username")
elem.clear()
try:
	elem.send_keys(username)
except:
	print("ERROR: you probably don't have 'username' defined in secrets.py")
	exit(0)
elem = browser.find_element_by_name("password")
try:
	elem.send_keys(password)
except:
	print("ERROR: you probably don't have 'password' defined in secrets.py")
	exit(0)
elem.send_keys(Keys.RETURN)
first_result = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_elements_by_partial_link_text('Calendar'))
button_to_calendar = browser.find_element_by_partial_link_text("Calendar")

main_window = browser.current_window_handle

button_to_calendar.send_keys(Keys.CONTROL + Keys.RETURN)

time.sleep(0.5)

calendar_events = browser.find_elements_by_class_name("fc-event-title")
calendar_events_temp = []
for i in range(len(calendar_events)):
	# This can an especially fragile part of the script. It only looks at
	# calendar events if it has string "Special Schedule" in it.
	if "Special Schedule" in calendar_events[i].text:
		calendar_events_temp.append(calendar_events[i])
calendar_events = calendar_events_temp
current_month_items = len(calendar_events)
this_month = datetime.datetime.now().strftime("%b")

################################
# Begin to loop through events #
################################
for i in range(current_month_items):
	fetch_special_schedule(i)
	time.sleep(2)


forwardback_buttons = browser.find_elements_by_class_name("fc-button-content")
for i in forwardback_buttons:
	if i.text == "Next":
		next_month_button = i
try:
	next_month_button
except NameError:
	next_month_button = forwardback_buttons[1]

next_month_button.click()

time.sleep(0.5)

calendar_events = browser.find_elements_by_class_name("fc-event-title")
calendar_events_temp = []
for i in range(len(calendar_events)):
	if "Special Schedule" in calendar_events[i].text:
		calendar_events_temp.append(calendar_events[i])
calendar_events = calendar_events_temp

for i in range(len(calendar_events)):
	fetch_special_schedule(i)
	time.sleep(2)

print("Success! {0}: {1} items; {2}: {3} items; Process took {4} seconds.".format(
		this_month, current_month_items, month_dict[datetime.datetime.now().month+1], len(calendar_events), (time.time()-start_time)))

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
	print("ERROR: you probably don't have 'ftp_username' or 'ftp_passwd' defined in secrets.py. These are the username and password to get into your FTP server for your website.")
	exit(0)

print("changing directory...")
ftp.cwd('/dailyschedule.atwebpages.com/scripts')

print("uploading schedules.json...")
ftp.storbinary("STOR schedules.json", open("schedules.json","rb"))

print("quitting FTP server...")
ftp.quit()


print("logging into GitHub...")
try:
	g = Github(gh_username, gh_password)
except:
	print("ERROR: you probably don't have 'gh_username' or 'gh_password' defined in secrets.py. PyGithub is also used to host schedules.json")
	exit(0)
print("searching for elearning repo...")
for repo in g.get_user().get_repos():
	if repo.name == "elearning":
		print("found elearning repo")
		print("committing schedules.json...")
		file = repo.get_file_contents("/schedules.json")
		repo.update_file("/schedules.json", "this commit is an update", open("schedules.json","rb").read(), file.sha)
		print("finished!")
