from fastapi import FastAPI, Request
import uuid
import uvicorn
import httpx
import asyncio
import multiprocessing
import threading

from master_logger.master_logger import Logger  # Assuming same path or pip install

logger = Logger()
app = FastAPI()

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Middleware to add request_id to execution_context."""
    request_id = str(uuid.uuid4())  # Generate a unique request ID
    logger.set_execution_context(request_id)  # Set the request_id in the logger's context
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    """Route handler that logs a message with the request_id"""
    logger.debug(f"Calling Root Path")
    return {"message": "Hello World"}

def run_fastapi():
    """Function to run FastAPI app"""
    uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False)

# Normal way to run fastapi server:
#
# def run_fastapi():
#     """Function to run FastAPI app"""
#     uvicorn.run(app, host="127.0.0.1", port=8000)
#
# if __name__ == "__main__":
#     # Run FastAPI server in a separate thread
#     run_fastapi()
#
#


# This part creates another process to make request to the fastapi server we are making.
# We should see logs like
#[2025-04-12 10:45:32][DEBUG][7fee3862-246c-46c2-86ee-1cf99836697f][root:25] Calling Root Path   -> Server Log
# Request 1 returned Response: {'message': 'Hello World'}                                        -> Client Log
# [2025-04-12 10:45:32][DEBUG][527f0039-66e8-4ef0-ab94-4a2d3dfbbc49][root:25] Calling Root Path
# Request 2 returned Response: {'message': 'Hello World'}
# [2025-04-12 10:45:32][DEBUG][e677be49-1015-47bc-8d00-a39510c4295a][root:25] Calling Root Path
# Request 3 returned Response: {'message': 'Hello World'}


async def make_sequential_requests():
    await asyncio.sleep(1)  # Let server start
    async with httpx.AsyncClient() as client:
        for i in range(1, 4):
            # Make requests without setting the request_id manually
            response = await client.get("http://127.0.0.1:8000/")  # FastAPI default port
            print(f"Request {i} returned Response: {response.json()}")


def make_request_in_new_process():
    """Function that runs in a new process and makes requests to the FastAPI app."""
    # Run the sequential requests
    asyncio.run(make_sequential_requests())

if __name__ == "__main__":
    # Run FastAPI server in a separate thread (daemonized)
    thread = threading.Thread(target=run_fastapi, daemon=True)
    thread.start()

    # Start a new process to make requests
    process = multiprocessing.Process(target=make_request_in_new_process)
    process.start()
    process.join()