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
    with open(pathToConfigFile, "w") as f:
        json.dump(defaultConfig, f)

with open(pathToConfigFile, "r") as f:
    config = json.load(f)

def getConfigAsJson():
    return json.dumps(config)

