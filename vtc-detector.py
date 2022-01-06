# coding: utf-8

import sys, os
import json, requests
from subprocess import Popen, PIPE
import re
import time, hashlib, hmac

# check env
envApiUrl = os.environ.get('VTC_API_URL')
envApiKey = os.environ.get('VTC_API_APIKEY')
envApiSecretKey = os.environ.get('VTC_API_SECRETKEY')
pathKeyValues = "/service/v1/keyValues"
keyValuesKey = os.environ.get('VTC_API_KEY')
if envApiUrl == None or envApiKey == None or envApiSecretKey == None:
    print("This program needs env VTC_API_URL and VTC_API_APIKEY and VTC_API_SECRETKEY.")
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


def generateHeaders(method, path):
    timestamp = str(int(time.time() * 1000))
    text = timestamp + method + path
    sign = hmac.new(envApiSecretKey, text, hashlib.sha256).hexdigest()
    return {
        'Content-Type': 'application/json',
        'X-API-KEY': envApiKey,
        'X-API-SIGN': sign,
        'X-API-TIMESTAMP': timestamp
    }

def getState():
    headers = generateHeaders("GET", pathKeyValues + "/" + keyValuesKey)
    response = requests.get(envApiUrl + pathKeyValues + "/" + keyValuesKey, headers=headers)
    data = json.loads(response.text)
    state = None
    url = None
    if 'value' in data:
        value = json.loads(data['value'])
        if 'state' in value:
            state = value['state']
        if 'url' in value:
            url = value['url']
    return state, url, data

def setState(state, getStateData):
    value = json.loads(getStateData['value'])
    value['state'] = state
    print(value)
    payload = {"value" : json.dumps(value), "updatedAt" : getStateData["updatedAt"]}
    print(payload)
    headers = generateHeaders("PUT", pathKeyValues + "/" + keyValuesKey)
    response = requests.put(envApiUrl + pathKeyValues + "/" + keyValuesKey, headers=headers, data=json.dumps(payload))
    data = json.loads(response.text)
    return data

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
getStateResult = getState()
state = getStateResult[0]
url = getStateResult[1]
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
        result = setState(dataReact[targetKey]["next"], getStateResult[2])
        print("setState response is ")
        print(result)
        killProcess(lockPID)
    elif targetKey == "end":
        lockPID = createLock()
        print("create lock pid " + lockPID)
        print("url is " + url)
        browserPID = getBrowserPID(url)
        print("browser pid is " + browserPID)
        for pid in browserPID.splitlines():
            print("iterate pid " + pid)
            killProcess(pid)
        setHDMIOff()
        print("set next state " + dataReact[targetKey]["next"])
        result = setState(dataReact[targetKey]["next"], getStateResult[2])
        print("setState response is ")
        print(result)
        killProcess(lockPID)
    else:
        sys.exit(0)
