# daily-schedule
This is a personal project I made on the side. A public version for fetching special schedules is WIP.

![image](https://github.com/rodrigo-castellon/daily-schedule/blob/master/sitescreenshot.png)

## Prerequisites
- [selenium 3.7.0](https://pypi.python.org/pypi/selenium)
- [PyGithub 1.35](https://pypi.python.org/pypi/PyGithub)

## Installation
1. Clone the repo: `$ git clone https://github.com/rodrigo-castellon/daily-schedule.git`
2. Download ChromeDriver from [the official ChromeDriver download page](https://sites.google.com/a/chromium.org/chromedriver/downloads).
3. Move ChromeDriver file to project directory.
4. Edit `secrets.py` to your own credentials.

## Short Example
```
import page_fetch as pf

schedules = pf.fetch() # note this process takes about ~1-2 minutes and will open a virtual chrome window

print(schedules)
```
