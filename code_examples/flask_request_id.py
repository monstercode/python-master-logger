
from flask import Flask, request
import uuid
import threading
import time
import requests

from master_logger.master_logger import Logger  # Assuming it's pip-installable or in PYTHONPATH

log = Logger()

app = Flask(__name__)

@app.before_request
def assign_request_id():
    request.request_id = str(uuid.uuid4())
    log.logger.info(f"Assigned request ID: {request.request_id}")

@app.route("/")
def hello():
    log.logger.info("Handling request in / route")
    return {"message": "Hello from Flask!", "request_id": request.request_id}


def run_server():
    log.logger.info("Starting Flask server")
    app.run(port=5001)


def make_request():
    # Give server a moment to start
    time.sleep(1)
    log.logger.info("Sending request to Flask server")
    response = requests.get("http://127.0.0.1:5001/")
    log.logger.info(f"Received response: {response.json()}")


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    make_request()