import socket
import sys
import struct
import pyaudio
from _thread import *
import threading
import datetime
import configControler
import json
import time
import uuid
import connectionControler
from pytz import timezone

config = configControler.config
connectionControler.removeAllConnections()

if config["isUdp"] == False:
   s = socket.socket()
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   s.bind(('', 4001))
   s.listen(5)

if config["isUdp"] == True:
   sTcp = socket.socket()
   sTcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   sTcp.bind(('', 4001))
   sTcp.listen(5)

   s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   s.bind(('', 4000))

def acknowledge(c, addr, id):
   hasSentInitialData = False

   print("Waiting for acknowledgment...")
   while True:
      data = c.recv(1024)

      acknowledgment, recordedData = tryToExtractAcknowledgment(data)
      print(acknowledgment)

      if(hasSentInitialData or acknowledgment != None):
         hasSentInitialData = True

         print("Received acknowledgement")
         print("Username: " + acknowledgment[0])

         #print(data)
         connectionInfo = connectionControler.addOrUpdateMicrophoneConnection(id, addr, acknowledgment)
         startTimeString = connectionInfo[connectionControler.STARTTIME]
         print("Datetime: " + startTimeString)
         return acknowledgment, startTimeString

def tryToExtractAcknowledgment(data):
   initialData = data[:25].decode()
   acknowledgment = None
      
   acknowledgment = initialData.split(";")

   return acknowledgment, data[25:]


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

if(config["isUdp"] == True):
   start_new_thread(acknowledgeThread, ())

lo = 0

while True:
   if config["isUdp"] == False:
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
         # print(data)
         acknowledgment, recordedData = tryToExtractAcknowledgment(data)

         startTime = datetime.datetime.fromtimestamp(int(acknowledgment[1])/1000.0, tz=timezone("Europe/Amsterdam"))

         connectionInfo = connectionControler.addOrUpdateMicrophoneConnection(str(uuid.uuid4()), address, acknowledgment)
         startTimeString = connectionInfo[connectionControler.STARTTIME]

         lo += len(data)
         f = None
         #print(acknowledgment)
         print(knownClients)
         if(acknowledgment[0] in knownClients):
            if (acknowledgment[0] in filesDict):
               f = filesDict[acknowledgment[0]]

            else:
               f = open("./" + acknowledgment[0] + "-" + startTimeString + ".pcm", "ab")

         #print(recordedData)
         

         #write json info
         writeJsonInfo(connectionInfo, acknowledgment)

         #write pcm file
         f.write(recordedData)
         print(lo)




      

   




      
