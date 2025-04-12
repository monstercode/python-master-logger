
from flask import Flask, request
import uuid
import threading
import time
import requests

# Don't log Flask logs like "GET / HTTP/1.1" 200. The Logger works without werkzeug logs. But you can keep it on.
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from master_logger.master_logger import Logger

logger = Logger()

app = Flask(__name__)

@app.before_request
def assign_request_id():
    request.request_id = str(uuid.uuid4())
    # alternatively:
    # logger.set_execution_context(request_id)

@app.route("/")
def root():
    logger.info("Got a request at /")
    some_function()
    logger.info("returning from /")
    return {"message": "Hello from Flask!", "request_id": request.request_id}



def run_server():
    app.run(port=5001)

def some_function():
    logger.debug("Im calling some_function")

def make_request():
    # Give server a moment to start
    time.sleep(1)
    requests.get("http://127.0.0.1:5001/")


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    make_request()

# Expected output, something like this:
# [2025-04-12 11:00:21][INFO][020b0a74-f9b5-41b0-a19b-b9344c76d0dc][root:27] Got a request at /
# [2025-04-12 11:00:21][DEBUG][020b0a74-f9b5-41b0-a19b-b9344c76d0dc][some_function:38] Im calling some_function
# [2025-04-12 11:00:21][INFO][020b0a74-f9b5-41b0-a19b-b9344c76d0dc][root:29] returning from /
