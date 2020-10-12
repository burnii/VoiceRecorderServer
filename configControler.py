from __future__ import print_function
import logging
import sys
import json
import os.path

# ConfigKeys
SAMPLE_RATE = "sampleRate"
ISUDP = "isUdp"
ID = "id"

defaultConfig = {
    SAMPLE_RATE: 44100,
    ISUDP: False
}

config = None

pathToConfigFile = "config.json"

if(not os.path.isfile(pathToConfigFile)):
    writeConfig(defaultConfig)

with open(pathToConfigFile, "r") as f:
    if(f.read() == ""):
        config = defaultConfig
    else:
        config = json.load(f)
    

def getConfigAsJson():
    return json.dumps(config)

def updateConfig(newConfig):
    config = newConfig
    writeConfig(config)

def writeConfig(conf):
    with open(pathToConfigFile, "w") as f:
        json.dump(conf, f)

