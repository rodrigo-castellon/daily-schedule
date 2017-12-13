# daily-schedule
This is a personal project I made on the side. A public version for fetching special schedules is WIP.

![image](https://github.com/rodrigo-castellon/daily-schedule/blob/master/sitescreenshot.png)

## Prerequisites
- [selenium 3.7.0+](https://pypi.python.org/pypi/selenium)
- [PyGithub 1.35+](https://pypi.python.org/pypi/PyGithub)

## Installation
1. Clone the repo: `$ git clone https://github.com/rodrigo-castellon/daily-schedule.git`
2. Download ChromeDriver from [the official ChromeDriver download page](https://sites.google.com/a/chromium.org/chromedriver/downloads).
3. Move ChromeDriver file to project directory.
4. Edit `secrets.py` to your own credentials.

## Short Example
```
>>> import page_fetch as pf
>>> schedules = pf.fetch() # note this process takes about ~1-2 minutes and will open a virtual chrome window
logging in...
Fetching special schedule 1 of 2
Date: Wednesday, Nov 29, 2017
Waiting for google doc login...
going back...
Fetching special schedule 2 of 2
Date: Wednesday, Dec 13, 2017
going back...
Success! Dec: 2 items; Jan: 0 items; Process took 82.0867300034 seconds.
>>> print(schedules) # 'schedules' is a JSON object, where each parent key is the date of the special schedule
{u'Tuesday, Nov 21, 2017': {u'url': u'https://docs.google.com/document/d/12k-mz12aLoYSdF2E2ZHufpf2n6XKMf-fVLlb9JZ3pH0/edit', u'date': 21, u'month_num': 11, u'title': u'Special Schedule: PCTV & Dance, Etc.', u'schedule': {u'Dance,Etc.': [u'9:41', u'10:37'], u'1': [u'8:10', u'8:48'], u'3': [u'10:42', u'11:20'], u'2': [u'8:53', u'9:31'], u'5': [u'12:08', u'12:46'], u'4': [u'11:25', u'12:03'], u'7': [u'1:34', u'2:12'], u'6': [u'12:51', u'1:29'], u'9': [u'3:00', u'3:38'], u'8': [u'2:17', u'2:55'], u'PCTV': [u'9:31', u'9:36']}}, u'Wednesday, Dec 13, 2017': {u'url': u'https://docs.google.com/document/d/1l8MlI3Xmbav3Q5fjQjSb39i_9ZB8MphX-Tl_iPAyaPU/edit', u'date': 13, u'month_num': 12, u'title': u'Special Schedule: StuCo Event & PCTV Special', u'schedule': {u'StuCoEvent': [u'8:10', u'8:41'], u'1': [u'8:46', u'9:24'], u'3': [u'10:42', u'11:20'], u'2': [u'9:29', u'10:07'], u'5': [u'12:08', u'12:46'], u'4': [u'11:25', u'12:03'], u'7': [u'1:34', u'2:12'], u'6': [u'12:51', u'1:29'], u'9': [u'3:00', u'3:38'], u'8': [u'2:17', u'2:55'], u'PCTV': [u'10:07', u'10:37']}}, u'Wednesday, Nov 29, 2017': {u'url': u'https://docs.google.com/document/d/1hWbS1wwiqoY7ei1jQFAMZkx7gmNNX20MlOzVojr7q_E/edit', u'date': 29, u'month_num': 11, u'schedule': {u'9thGradeElections': [u'9:40', u'10:20'], u'1': [u'8:10', u'8:50'], u'3': [u'10:25', u'11:05'], u'2': [u'8:55', u'9:35'], u'5': [u'11:55', u'12:35'], u'4': [u'11:10', u'11:50'], u'7': [u'1:25', u'2:05'], u'6': [u'12:40', u'1:20'], u'9': [u'2:55', u'3:38'], u'8': [u'2:10', u'2:50']}, u'title': u'Special Schedule: Spark Break / 9th Grade Elections'}, u'Tuesday, Nov 7, 2017': {u'url': u'https://docs.google.com/document/d/1WwOW9sMlBSv9yLRpTb1N-SBeV892wX8r2bYyw2AEfCU/edit', u'date': 7, u'month_num': 11, u'schedule': {u'ASSEMBLY': [u'9:47', u'10:23'], u'1': [u'8:10', u'8:50'], u'3': [u'10:28', u'11:08'], u'2': [u'8:55', u'9:35'], u'5': [u'11:58', u'12:38'], u'PCTV': [u'9:35', u'9:42'], u'7': [u'1:28', u'2:08'], u'6': [u'12:43', u'1:23'], u'9': [u'2:58', u'3:38'], u'8': [u'2:13', u'2:53'], u'4': [u'11:13', u'11:53']}, u'title': u"Special Schedule: Veteran's Day"}, u'Wednesday, Nov 15, 2017': {u'url': u'https://docs.google.com/document/d/12B-xLLdAdq7NMu_lir9M9Z7erSzfI48i5NB0kOouqmI/edit', u'date': 15, u'month_num': 11, u'schedule': {u'BetaClubInductions-ICI': [u'9:40', u'10:23'], u'1': [u'8:10', u'8:50'], u'3': [u'10:28', u'11:08'], u'2': [u'8:55', u'9:35'], u'5': [u'11:58', u'12:38'], u'4': [u'11:13', u'11:53'], u'7': [u'1:28', u'2:08'], u'6': [u'12:43', u'1:23'], u'9': [u'2:58', u'3:38'], u'8': [u'2:13', u'2:53']}, u'title': u'Special Schedule: Beta Club Inductions'}, u'Wednesday, Nov 1, 2017': {u'url': u'https://docs.google.com/document/d/1G3qYpRRgh7r-EmktYCJ-zSkKOi0yNtbqRBqX5v4y074/edit', u'date': 1, u'month_num': 11, u'schedule': {u'ASSEMBLY': [u'12:57', u'2:12'], u'1': [u'8:10', u'8:46'], u'3': [u'9:32', u'10:08'], u'2': [u'8:51', u'9:27'], u'5': [u'10:54', u'11:30'], u'4': [u'10:13', u'10:49'], u'7': [u'12:16', u'12:52'], u'6': [u'11:35', u'12:11'], u'9': [u'3:00', u'3:38'], u'8': [u'2:17', u'2:55']}, u'title': u'Special Schedule: Incognito'}, u'Wednesday, Nov 8, 2017': {u'url': u'https://docs.google.com/document/d/1ylqI6FxxqQYJ-zoEK7AzxlNE2itjvOnKjTqcEMEqGmc/edit', u'date': 8, u'month_num': 11, u'title': u'Special Schedule: US Musical Assembly', u'schedule': {u'Assembly': [u'9:36', u'10:37'], u'1': [u'8:10', u'8:48'], u'3': [u'10:42', u'11:20'], u'2': [u'8:53', u'9:31'], u'5': [u'12:08', u'12:46'], u'4': [u'11:25', u'12:03'], u'7': [u'1:34', u'2:12'], u'6': [u'12:51', u'1:29'], u'9': [u'3:00', u'3:38'], u'8': [u'2:17', u'2:55']}}, u'Tuesday, Nov 14, 2017': {u'url': u'https://docs.google.com/document/d/1p2Eo5ivf2e923fDi-gXyeK_ttW-khbf3NUZ9ecrIV0o/edit', u'date': 14, u'month_num': 11, u'title': u'Special Schedule: PCTV + Advisory', u'schedule': {u'AdvisorySession1(A)': [u'9:41', u'10:08'], u'1': [u'8:10', u'8:48'], u'PCTV': [u'9:31', u'9:36'], u'3': [u'10:45', u'11:23'], u'2': [u'8:53', u'9:31'], u'5': [u'12:11', u'12:49'], u'AdvisorySession2(B)': [u'10:13', u'10:40'], u'7': [u'1:37', u'2:15'], u'6': [u'12:54', u'1:32'], u'9': [u'3:03', u'3:38'], u'8': [u'2:20', u'2:58'], u'4': [u'11:28', u'12:06']}}}
```
