# coding: utf-8

import sys, os, datetime, time
import json, requests
from subprocess import Popen, PIPE
import re

# check env
envApiUrl = os.environ.get('VTC_API_URL')
envApiKey = os.environ.get('VTC_API_KEY')
if envApiUrl == None or envApiKey == None:
    print("This program needs env VTC_API_URL and VTC_API_KEY.")
    sys.exit(1)

# check argv
# arg[1] needs string to react (json format)
#   for server on  {"start":{"check":"closed","next":"request to open"}}
#   for server off {"end":{"check":"opened","next":"request to close"}}
#   for client     {"start":{"check":"request to open","next":"opened"},"end":{"check":"request to close","next":"closed"}}
if len(sys.argv) != 2:
    print("This program needs arg[1] for state string to react.")
    sys.exit(2)
dataReact = json.loads(sys.argv[1])

# create headers
apiHeaders = {
    'Content-Type': 'application/json',
    'x-api-key': envApiKey
}


def getState():
    response = requests.get(envApiUrl + "/state", headers=apiHeaders)
    data = json.loads(response.text)
    result = None
    if 'state' in data:
        result = data['state']
    return result

def setState(state):
    payload = {"value" : state}
    response = requests.put(envApiUrl + "/state", headers=apiHeaders, data=json.dumps(payload))
    data = json.loads(response.text)
    return data

def getURL():
    response = requests.get(envApiUrl + "/url", headers=apiHeaders)
    data = json.loads(response.text)
    result = ""
    if 'url' in data:
        result = data['url']
    return result

def getLockPID():
    cmd = "ps -aux | grep '[p]ython /home/pi/while-loop.py' | awk {'print $2'}"
    proc = Popen(cmd, shell = True, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    stdout_data, stderr_data = proc.communicate()
    result = ""
    if stdout_data != "":
        result = stdout_data
    return result

def killProcess(pid):
    print("Kill process. PID is " + pid)
    cmd = "kill " + pid
    proc = Popen(cmd, shell = True, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    return

def createLock():
    proc = Popen(["python", "/home/pi/while-loop.py"], stdout=PIPE, stderr=PIPE)
    return str(proc.pid)

def setHDMIOn():
    # power on
    cmd = "echo 'on 0' | cec-client -s"
    proc = Popen(cmd, shell = True, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    stdout_data, stderr_data = proc.communicate()
    print("=== log HDMI on start ===")
    print(stdout_data)
    print("=== log HDMI on err ===")
    print(stderr_data)
    print("=== log HDMI on end ===")
    time.sleep(5)
    # source self HDMI
    cmd = "echo 'as 0' | cec-client -s"
    #cmd = "echo 'tx 1f:82:20:00' | cec-client -s"
    proc = Popen(cmd, shell = True, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    stdout_data, stderr_data = proc.communicate()
    print("=== log HDMI as start ===")
    print(stdout_data)
    print("=== log HDMI as err ===")
    print(stderr_data)
    print("=== log HDMI as end ===")
    return

def setHDMIOff():
    # power off
    cmd = "echo 'standby 0' | cec-client -s"
    proc = Popen(cmd, shell = True, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    stdout_data, stderr_data = proc.communicate()
    print("=== log HDMI standby start ===")
    print(stdout_data)
    print("=== log HDMI standby err ===")
    print(stderr_data)
    print("=== log HDMI standby end ===")
    return

def wakeupBrowser(url):
    proc = Popen("sudo -u pi DISPLAY=:0 chromium-browser --start-maximized '" + url + "'", shell = True, stdout=PIPE, stderr=PIPE)
    return str(proc.pid)

def getBrowserPID(url):
    cmd = "ps -aux | grep [c]hromium-browser | grep " + url + " | awk {'print $2'}"
    proc = Popen(cmd, shell = True, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    stdout_data, stderr_data = proc.communicate()
    result = ""
    if stdout_data != "":
        result = stdout_data
    return result

# check current state
state = getState()
targetKey = None
print(state)
for key in dataReact:
    if dataReact[key]["check"] == state:
        targetKey = key
        print("hit react")
        print(dataReact[targetKey])
        break
if targetKey == None:
    sys.exit(0)

print("### " + str(datetime.datetime.now()))

lockPID = getLockPID()
print("lock PID " + lockPID)
if lockPID != "":
    print("lock exists.")
    sys.exit(0)
else:
    print("lock not exists.")
    if targetKey == "start":
        lockPID = createLock()
        print("create lock pid " + lockPID)
        url = getURL()
        print("url is " + url)
        pattern = '[^\w:/\.\?=&]'
        result = re.search(pattern, url)
        if result:
            print("can't use char " + result.group())
            killProcess(lockPID)
            sys.exit(1)
        setHDMIOn()
        browserPID = wakeupBrowser(url)
        print("browser pid is " + browserPID)
        print("set next state " + dataReact[targetKey]["next"])
        result = setState(dataReact[targetKey]["next"])
        print("setState response is ")
        print(result)
        killProcess(lockPID)
    elif targetKey == "end":
        lockPID = createLock()
        print("create lock pid " + lockPID)
        url = getURL()
        print("url is " + url)
        browserPID = getBrowserPID(url)
        print("browser pid is " + browserPID)
        for pid in browserPID.splitlines():
            print("iterate pid " + pid)
            killProcess(pid)
        setHDMIOff()
        print("set next state " + dataReact[targetKey]["next"])
        result = setState(dataReact[targetKey]["next"])
        print("setState response is ")
        print(result)
        killProcess(lockPID)
    else:
        sys.exit(0)
