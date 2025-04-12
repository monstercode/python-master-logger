# A Master Logger for python

A Logger singleton that is used through all the application to have consistent log format and set execution context
variables or information. The Logger is thread-safe and coroutines safe (through contextvars). You can use it with asyncio, Flask, Fastapi or plain python.

**Requires Python > 3.7**

## Why use this logger?
Make your logs look uniform, with execution context automatically added, like from what Class and method the log is being done.


The logs follow this format:

```
[<datetime>][<context-execution>][<Class>][<method>][<context-value>] <Message>
```

### Simple example comparison

Using the plain Python logging:
```
[2025-03-11 22:06:44.908590][WARNING] The user with id 156874 was not found.
```
V.S.

Using this Logger:
```
[2025-03-11 22:06:44.908590][WARNING][request-d042a634-1a7d-4495-9296-9215d729e4f8][GoogleService][get_user][Account id: 54] The user with id 156874 was not found.
```
We can get much more execution context while doing the same logging call `logger.warning(f"The user with id {id} was not found")`, but with this logger we know exactly from where it was called and have more context, like the request id, the class and method, and even set context variables like the account id, without passing it around through all the code. Very useful for checking logs while debugging.

## How to use this Logger?

The simplest way to use it, just copy the `master_logger/master_logger.py` to your project. No dependencies required, it only uses std lib python modules.

In your code just make 
```
logger = Logger(log_line_number=True, logger_level=logging.DEBUG)
 - log_line_number: bool | wether we should add the line number of the code or not
 - logger_level: int | the standar logging levels | logging.DEBUG | logging.INFO | logging.ERROR etc
```
Once set in the first instance of the singleton is created, we don't change this parameters.


## Setting context manually
`set_execution_context` This method set the context of execution. if you have several cronjobs for example, you can set the name of the cronjob to know that all logs come from that cronjob. If you use the Flask request id snippet below, that would be used instead (to search all the logs of a specific request easily).
```
logger.set_execution_context("backup-cronjob")

# all log calls after this will have the ["backup-cronjob"] added to the log
```
`set_context_key` This method sets a context key you define (optionally). Typically it could be a user id, an account id or any key that associated all subsequent calls and executions. If you set it in coroutines, each coroutine has their own context key, so they don't overlap and can be used as a global variable associated to that context. The same applies for threads.
```
logger.set_context_key(f"account_id: {account_id}")

# all log calls after this will have the ["account_id: {account_id}"] added to the log. 
# If after a certain point you need to remove it, call the method with an empty string ""
# The variable is overwritten every time you call (in the current execution context, like the coroutine context) 
# This doesn't affect other coroutines or threads. 
```

### Flask request id snippet
To set a unique request id per request, add this snippet to your code:

```
    from flask import Flask, request
        import uuid

        app = Flask(__name__)

        @app.before_request
        def assign_request_id():
            request.request_id = str(uuid.uuid4()) 
```

### FastAPI request id snippet

```
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Middleware to add request_id to execution_context."""
    request_id = str(uuid.uuid4())  # Generate a unique request ID
    logger.set_execution_context(request_id)  # Set the request_id in the logger's context
    response = await call_next(request)
    return response
```

The Logger class mimics the standard methods from the logging module

```
def debug(self, message):
	...
def info(self, message):
	...
def warning(self, message):
	...
def error(self, message):
	...
def critical(self, message):
	...
def exception(self, message):
    # aware of the exception context. It logs the traceback like python logging lib.
```

## Examples

Check in the `code_examples` folder some usage examples. run them like:
```
python3 -m code_examples.asyncio_example 
python3 -m code_examples.class_example
python3 -m code_examples.singleton_example
```
