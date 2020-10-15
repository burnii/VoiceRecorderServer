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

config = defaultConfig

pathToConfigFile = "config.json"

def writeConfig(conf):
    with open(pathToConfigFile, "w") as f:
        json.dump(conf, f)

if(not os.path.isfile(pathToConfigFile)):
    writeConfig(defaultConfig)

with open(pathToConfigFile, "r") as f:
    if(f.read() == ""):
        config = defaultConfig
    else:
        f.seek(0)
        config = json.load(f)
    

def getConfigAsJson():
    return json.dumps(config)

def updateConfig(newConfig):
    newConfig[ISUDP] = (newConfig[ISUDP] == "true")
    config = newConfig
    writeConfig(config)



