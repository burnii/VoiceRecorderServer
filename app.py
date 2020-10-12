from flask import Flask, request
from flask_cors import CORS, cross_origin
import sys
import configControler
app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})

@app.route("/connections")
def get_connections():
    return open("./connections.json", "r").read()

@app.route("/config")
def get_config():
    return open("./config.json", "r").read()

@app.route("/updateConfig", methods = ["POST"])
def post_config():
    configControler.updateConfig(request.form)
    return "asd"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)