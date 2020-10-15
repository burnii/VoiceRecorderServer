import sys
import json
import os.path
import datetime
from pytz import timezone

# ConfigKeys
UUID = "uuid"
ADDRESS = "address"
NAME = "name"
DEVICE = "device"
STARTTIME = "starttime"
ENDTIME = "endtime"
LOSTPACKAGES = "lostpackages"
SENTPACKAGES = "sentpackages"

config = None

connectionInfo = []

pathToConnectionsFile = "connections.json"

def updateSerializedConnections():
    global connectionInfo
    #print(connectionInfo)
    with open(pathToConnectionsFile, "w") as f:
        json.dump(connectionInfo, f)

def addOrUpdateMicrophoneConnection(id, addr, acknowledgement):
    global connectionInfo
    startTime = datetime.datetime.fromtimestamp(int(acknowledgement[1])/1000.0, tz=timezone("Europe/Amsterdam"))
    startTimeString = startTime.strftime("%d%m%Y%M%H%S")
    #print(startTimeString)

    i = getIndexOfConnectionname(acknowledgement[0])

    if i == None:
        print("add connection with", id)
        connectionInfo.append({
            UUID: id,
            ADDRESS: addr[0],
            NAME: acknowledgement[0],
            DEVICE: acknowledgement[2],
            STARTTIME: startTimeString,
            ENDTIME: startTimeString,
            LOSTPACKAGES: 0,
            SENTPACKAGES: 0
        })

        i = len(connectionInfo) - 1
    else:
        #print("update connection: ", i, " ", acknowledgement[0])
        #print(acknowledgement)
        connectionInfo[i][DEVICE] = acknowledgement[2]
        connectionInfo[i][ENDTIME] = startTimeString

    updateSerializedConnections()  
    
    return connectionInfo[i]

def getIndexOfConnectionname(name):
    global connectionInfo

    for i in range(len(connectionInfo)):
        if(connectionInfo[i][NAME] == str(name)):
            return i

    return None

def removeMicrophoneConnection(id):
    global connectionInfo

    for i in range(len(connectionInfo)):
        if(connectionInfo[i][UUID] == id):
            del connectionInfo[i]
            break

    updateSerializedConnections()

def removeAllConnections():
    global connectionInfo

    for i in range(len(connectionInfo)):
        del connectionInfo[i]
            
    updateSerializedConnections()

updateSerializedConnections()

