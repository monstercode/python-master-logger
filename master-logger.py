import logging
import inspect
from flask import Request


class Logger:
    """This is an app level Logger class singleton shared among all services. It's not thread-safe.

    The idea is logging in a consistent formart like 
        [<datetime>][<context-execution>][<Class>][<method>][<context-value>] <Message>
    
    context-execution: cron|request_id|etc
    context-value: account_id|jira_ticket_key|user_id|etc


    If you are in a request context, set to the flask request a request_id variable to search logs by a specific request
    Add this piece of code to set the request id to uniquely identify requests
    
        from flask import Flask, request
        import uuid

        app = Flask(__name__)

        @app.before_request
        def assign_request_id():
            request.request_id = str(uuid.uuid4()) 


    Be careful, we use it globally, so we can trace by context key without explicitly passing the key to the 
    lower level services that shouldn't be aware of the context. As all execution is sequential, there
    is no race condition that would invalidate the current context key. The processing function that
    retrieves the context and sends to process has to set the key beforehand, and all subsequent execution
    will have the current context key.

    !IMPORTANT NOTE: If we move to multithread/parallelism, this has to be revised. 
    We probably would need one logger per thread

    """

    SINGLETON_INSTANCE = None

    def __init__(self):
        self.context_key = ""
        self.execution_context = "cron"
        logging.basicConfig(format="[%(asctime)s][%(levelname)s]%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger("master-logger")
        self.logger.setLevel(logging.DEBUG)

    def __new__(cls):
        """This method makes the service a Singleton, so that once the context_key is set, it's not lost
            when importing the logger from several modules
        """
        if not cls.SINGLETON_INSTANCE:
            cls.SINGLETON_INSTANCE = super(Logger, cls).__new__(cls)
        return cls.SINGLETON_INSTANCE

    def set_context_key(self, context_key: str):
        """Set the context key of the execution (account id, user id, jira key, etc)"""
        self.context_key = context_key

    def set_execution_context(self, execution_context: str):
        """Set the execution context, wether is from a cronjob, webserver or whatever"""
        self.execution_context = execution_context

    def _get_service_caller_from_stack(self):
        """Inspect the call stack to know where is this log being executed from automatically, retrieve class and method"""
        stack = inspect.stack()
        method_name = None
        instance_class = None

        for i in range(len(stack)-1):
            # Iterate through the stack calls. If the current frame is for Logger, skip
            if type(stack[i][0].f_locals.get("self")) is Logger:
                continue

            # We got our first frame that is not from the Logger execution
            method_name = stack[i][0].f_code.co_name

            if type(stack[i+1][0].f_locals.get("req", None)) is Request:
                # If we are in a controller call, get the path for the request
                instance_class = stack[i+1][0].f_locals["req"].path
            else:
                # When using a static method, the frame we get is from a decorator, so we have to use the next frame
                grab_from_stack = stack[i][0].f_locals if stack[i][0].f_locals else stack[i+1][0].f_locals

            if not instance_class:
                instance_class = next(iter(grab_from_stack.values()))
                if hasattr(instance_class, "__name__"):
                    instance_class = instance_class.__name__
                elif hasattr(instance_class, "__class__"):
                    instance_class = instance_class.__class__.__name__

            break
        return instance_class, method_name

    def _get_context_string(self):
        """Prepare the prefix with service and context key, if any"""
        prefix = ""

        execution_context = None
        try:
            from flask import request
            execution_context = request.request_id
        except Exception:
            execution_context = self.execution_context

        try:
            service, method = self._get_service_caller_from_stack()
        except Exception:
            service, method = "", ""

        if execution_context:
            prefix += f"[{execution_context}]"
        if service and service != "Logger":
            prefix += f"[{service}]"
        if method and method != service:
            prefix += f"[{method}]"
        if self.context_key:
            prefix += f"[{self.context_key}]"

        return prefix

    def debug(self, message):
        self.logger.debug(f"{self._get_context_string()}{'' if message.startswith('[') else ' '}{message}")

    def info(self, message):
        self.logger.info(f"{self._get_context_string()}{'' if message.startswith('[') else ' '}{message}")

    def warning(self, message):
        self.logger.warning(f"{self._get_context_string()}{'' if message.startswith('[') else ' '}{message}")

    def error(self, message):
        self.logger.error(f"{self._get_context_string()}{'' if message.startswith('[') else ' '}{message}")

    def critical(self, message):
        self.logger.critical(f"{self._get_context_string()}{'' if message.startswith('[') else ' '}{message}")

    def exception(self, message):
        """This method should be used inside an exception handler.
        Yes, it is aware of the higher level exception, no need to pass it explicitly"""
        self.logger.exception(f"{self._get_context_string()}{'' if message.startswith('[') else ' '}{message}")