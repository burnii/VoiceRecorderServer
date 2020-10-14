import socket
import sys
import struct
import pyaudio
from _thread import *
import threading
import datetime
import connectionControler
import configControler
import json
import time
import uuid
from pytz import timezone

config = configControler.config
connectionControler.removeAllConnections()

if config["isUdp"] == False:
   print("Create tcp sockets")
   s = socket.socket()
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   s.bind(('', 4001))
   s.listen(5)

if config["isUdp"] == True:
   print("Create udp sockets")
   sTcp = socket.socket()
   sTcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   sTcp.bind(('', 4001))
   sTcp.listen(5)

   s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   s.bind(('', 4001))

def acknowledge(c, addr, id):
   hasSentInitialData = False

   #print("Waiting for acknowledgment...")
   while True:
      data = c.recv(1024)

      acknowledgment, recordedData = tryToExtractAcknowledgment(data)
      #print(acknowledgment)

      if(hasSentInitialData or acknowledgment != None):
         hasSentInitialData = True

         #print("Received acknowledgement")
         #print("Username: " + acknowledgment[0])

         #print(data)
         connectionInfo = connectionControler.addOrUpdateMicrophoneConnection(id, addr, acknowledgment)
         startTimeString = connectionInfo[connectionControler.STARTTIME]
         #print("Datetime: " + startTimeString)
         return acknowledgment, startTimeString

def tryToExtractAcknowledgment(data):
   initialData = data[:40].decode()
   acknowledgment = None
      
   acknowledgment = initialData.split(";")

   return acknowledgment, data[40:]


def tcpThread(c, addr, id):  
   print("Recording Thread started")

   # Try to set initial data
   acknowledgment, startTimeString = acknowledge(c, addr, id)
   
   i = connectionControler.getIndexOfConnectionname(acknowledgment[0])
   connectionInfo = connectionControler.connectionInfo[i]

   f = open("./" + acknowledgment[0] + "-" + connectionInfo[connectionControler.STARTTIME] + ".pcm", "ab")
   config = configControler.getConfigAsJson()
   c.send((config + "\n").encode("utf-8"))

   while(True):
      try:
         data = c.recv(1024)
      except:

         print("Connection lost with ", addr)
         connectionControler.removeMicrophoneConnection(id)
      if(data):
         # write json info
         writeJsonInfo(connectionInfo, acknowledgment)

         #write pcm file
         f.write(data)
            
def testConnectionThread(c, addr, id):
   print("Testconnection Thread started")
   while(True):
      time.sleep(10)
      print("Check connection with ", addr)
      try:
         c.send(b"dd")
         print("Connection still active with ", addr)
      except:
         print("Connection lost with ", addr)
         connectionControler.removeMicrophoneConnection(id)
         break

filesDict = {}
knownClients = {}

def writeJsonInfo(connectionInfo, acknowledgment):
   path = "./" + acknowledgment[0] + "-" + connectionInfo[connectionControler.STARTTIME] + ".json"
   with open(path, "w") as f:
      json.dump(connectionInfo, f)

def acknowledgeThread():
   while True:
      c, addr = sTcp.accept()
      id = str(uuid.uuid4())
      print ('Got connection from ', addr, " for acknowledgement")

      acknowledgment, startTimeString = acknowledge(c, addr, id)

      if(acknowledgment[0] not in knownClients):
         knownClients[acknowledgment[0]] = id
         config = configControler.getConfigAsJson()
         c.send((config + "\n").encode("utf-8"))




lo = 0

buffer = []
userNameBufferDict = {}
userNameLastPackageCount = {}

def writeUdpFilesThreadUsername(username):
   failedCount = 0

   last = time.time()
   while True:
      usernameBuffer = userNameBufferDict[username]

      for x in list(usernameBuffer):
         acknowledgment, recordedData = tryToExtractAcknowledgment(x)

         if acknowledgment[0] not in userNameLastPackageCount:
            userNameLastPackageCount[acknowledgment[0]] = 0
            #print("Set ", acknowledgment[0], "to ", 0)

         if int(acknowledgment[3]) == (int(userNameLastPackageCount[acknowledgment[0]]) + 1):
            failedCount = 0
            last = time.time()
            userNameLastPackageCount[acknowledgment[0]] = acknowledgment[3]

            connectionInfo = connectionControler.addOrUpdateMicrophoneConnection(str(uuid.uuid4()), address, acknowledgment)
            startTimeString = connectionInfo[connectionControler.STARTTIME]

            f = None
            #print(knownClients)
            if(acknowledgment[0] in knownClients):
               if (acknowledgment[0] in filesDict):
                  f = filesDict[acknowledgment[0]]
               else:
                  f = open("./" + acknowledgment[0] + "-" + startTimeString + ".pcm", "ab")
                  filesDict[acknowledgment[0]] = f

            #write json info
            writeJsonInfo(connectionInfo, acknowledgment)

            print("write ", len(recordedData), " to ", acknowledgment[0], " Nr: ", acknowledgment[3])
            #write pcm file
            f.write(recordedData)
            usernameBuffer.remove(x)
      
      failedCount += 1

      if(time.time() - last > 3 and len(usernameBuffer) > 0):
        for bla in usernameBuffer:
           ack, data = tryToExtractAcknowledgment(bla)
           print(ack)
        print(len(usernameBuffer))
        userNameLastPackageCount[username] = str(int(userNameLastPackageCount[username]) + 1)
        print("Increase count to ", userNameLastPackageCount[username])
        last = time.time()
        failedCount = 0

      


def writeUdpFilesThread():
   failedAttempts = 0
   while True:
      for x in list(buffer):
         acknowledgment, recordedData = tryToExtractAcknowledgment(x)

         if acknowledgment[0] not in userNameLastPackageCount:
            userNameLastPackageCount[acknowledgment[0]] = 0
            #print("Set ", acknowledgment[0], "to ", 0)

         print("looking for package count ", userNameLastPackageCount[acknowledgment[0]])

         if int(acknowledgment[3]) == (int(userNameLastPackageCount[acknowledgment[0]]) + 1 or failedAttempts > 10):
            failedAttempts = 0
            buffer.remove(x)
            userNameLastPackageCount[acknowledgment[0]] = acknowledgment[3]

            connectionInfo = connectionControler.addOrUpdateMicrophoneConnection(str(uuid.uuid4()), address, acknowledgment)
            startTimeString = connectionInfo[connectionControler.STARTTIME]

            f = None
            #print(knownClients)
            if(acknowledgment[0] in knownClients):
               if (acknowledgment[0] in filesDict):
                  f = filesDict[acknowledgment[0]]

               else:
                  f = open("./" + acknowledgment[0] + "-" + startTimeString + ".pcm", "ab")
                  filesDict[acknowledgment[0]] = f

            #write json info
            writeJsonInfo(connectionInfo, acknowledgment)

            print("write ", len(recordedData), " to ", acknowledgment[0], " Nr: ", acknowledgment[3])
            #write pcm file
            f.write(recordedData)

if(config["isUdp"] == True):
   start_new_thread(acknowledgeThread, ())
   #start_new_thread(writeUdpFilesThread, ())

count = 0

while True:
   if config["isUdp"] == False:
      print("Wait for tcp connection")
      c, addr = s.accept()
      id = str(uuid.uuid4())
      print ('Got connection from', addr)
      start_new_thread(tcpThread,(c, addr, id))
      start_new_thread(testConnectionThread, (c, addr, id))

   if config["isUdp"] == True:
      print("Waiting for UDP data")
      data, address = s.recvfrom(512)
      print("received", len(data), "from", address)

      if data:
         count = count + 1
         buffer.append(data)

         acknowledgment, recordedData = tryToExtractAcknowledgment(data)

         if acknowledgment[0] not in userNameBufferDict.keys():
            userNameBufferDict[acknowledgment[0]] = []
            print("Start new Udp Writing Thread for ", acknowledgment[0])
            start_new_thread(writeUdpFilesThreadUsername, (acknowledgment[0],))
            
         userNameBufferDict[acknowledgment[0]].append(data)

         print("Got ", len(data), acknowledgment[3])






      

   




      
