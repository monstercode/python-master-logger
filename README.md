# A Master Logger for python

A Logger class that is used through all the application to have consistent log format like this

```
[<datetime>][<context-execution>][<Class>][<method>][<context-value>] <Message>
```

Examples:

```
[2025-03-11 22:06:44.908590][request-d042a634-1a7d-4495-9296-9215d729e4f8][GoogleService][get_user][Account id: 54] The user with id 156874 was found.
....
[2025-03-11 22:06:44.908592][remove-licenses-cronjob][OktaService][block_user][User id: 48] The user with id 48 was succesfully blocked.
[2025-03-11 22:06:44.908592][remove-licenses-cronjob][GoogleService][remove_user_license][User id: 48] The user has no license assigned.
```

The purpose is to not pass all the required variable to make the logs and set a global context through the execution tree.

With this, we can inspect the execution tree and what happens through out several calls without losing some context of the execution, and pinning down the Class Service and method from where each log is called, instead of setting it manually in each message.

The Logger class is NOT thread-safe, unless we use an singleton instance per thread.


To set a unique request id per request, add this snippet to your code:

```
    from flask import Flask, request
        import uuid

        app = Flask(__name__)

        @app.before_request
        def assign_request_id():
            request.request_id = str(uuid.uuid4()) 
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
	# aware of the exception context
```