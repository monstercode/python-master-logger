import logging
import inspect
import contextvars


class Logger:
    """This is an app level Logger class singleton shared among all services.
    It's thread-safe using contextvars for global context execution
    and not pass around arguments only used by the logger but useful for logging context info.

    The idea is logging in a consistent format like
        [<datetime>][<context-execution>][<Class>][<method>][<context-value>] <Message>
    
    context-execution: <cronjob-name> | <request_id> | nothing
    context-value: an account_id| a jira_ticket_key | a user_id | nothing


    If you are using flask, set to the flask request a request_id attribute to search logs by a specific request
    Add this piece of code to set the request id to uniquely identify requests
    
        from flask import Flask, request
        import uuid

        app = Flask(__name__)

        @app.before_request
        def assign_request_id():
            request.request_id = str(uuid.uuid4())

    =============================================================

    For FastAPI add the middleware to set the request_id in the execution context.

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        # Middleware to add request_id to execution_context
        request_id = str(uuid.uuid4())  # Generate a unique request ID
        logger.set_execution_context(request_id)  # Set the request_id in the logger's context
        response = await call_next(request)
        return response

    """

    SINGLETON_INSTANCE = None # the Logger instance singleton
    INITIALIZED = False # if the Logger is initialized, __init__ is called every time after __new__.
        # This flag prevent to call __init__ on a second instantiation of the singleton


    def __init__(self, log_line_number=True, logger_level=logging.DEBUG):
        if self.INITIALIZED:
            # Do not overwrite the instance attributes of the singleton if already initialized.
            # This would empty the already set attributes
            return

        self.execution_context = contextvars.ContextVar("logger_exec_context", default="")
        self.context_key = contextvars.ContextVar("logger_context_key", default="")
        self.log_line_number = log_line_number

        logging.basicConfig(format="[%(asctime)s][%(levelname)s]%(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        self.logger = logging.getLogger("master-logger")
        self.logger.setLevel(logger_level)
        Logger.INITIALIZED = True

    def __new__(cls, log_line_number=True, logger_level=logging.DEBUG):
        """This method makes the service a Singleton"""
        if not cls.SINGLETON_INSTANCE:
            cls.SINGLETON_INSTANCE = super(Logger, cls).__new__(cls, )
        return cls.SINGLETON_INSTANCE

    def set_context_key(self, context_key: str):
        """Set the context key of the execution (account id, user id, jira key, etc)"""
        self.context_key.set(context_key)

    def set_execution_context(self, execution_context: str):
        """Set the execution context, whether is from a cronjob, webserver (specify a request id), etv)"""
        self.execution_context.set(execution_context)

    def get_execution_context(self) -> str:
        """Get the execution context, fallback to try getting the request id from Flask request"""

        execution_context = self.execution_context.get()
        if execution_context:
            return execution_context

        # is no execution context if set, try to check if we are in a request context and have a request_id
        try:
            from flask import has_request_context, request
            if has_request_context():
                return getattr(request, "request_id", "")
        except (ModuleNotFoundError, ImportError, RuntimeError, AttributeError):
            pass

        return ""

    def _get_caller_from_stack(self):
        """Inspect the call stack to know where is this log being executed from automatically,
        retrieve class, method or function and line number"""
        stack = inspect.stack()
        method_or_function_name = ""
        class_name = ""
        line_number = ""

        for i in range(len(stack)-1):
            # Iterate through the stack calls. If the current frame is for Logger, skip
            if type(stack[i][0].f_locals.get("self")) is Logger:
                continue

            # We got our first frame that is not from the Logger execution
            class_name = self._get_class_name(stack_frame=stack[i][0])
            method_or_function_name = stack[i][0].f_code.co_name
            line_number = stack[i][0].f_lineno
            break

        return class_name, method_or_function_name, line_number

    def _get_class_name(self, stack_frame) -> str:
        """We get the class name by the parameters of the function being called. If it's
        a static method or not bound to a class, we get nothing. Also, we rely on
        'self' and 'cls' parameter naming convention"""

        # Instance class name
        if 'self' in stack_frame.f_locals:
            return stack_frame.f_locals['self'].__class__.__name__

        # Class method class name
        elif 'cls' in stack_frame.f_locals:
            return stack_frame.f_locals['cls'].__name__

        # Not in a class/instance or calling a static method
        # Static methods do not have any implicit reference to the class they're defined in.
        return ""

    def _get_context_string(self) -> str:
        """Prepare the prefix with class+method or function, and context key, if any"""
        prefix = ""

        execution_context = self.get_execution_context()

        try:
            class_name, method_or_function_name, line_number= self._get_caller_from_stack()
        except Exception:
            class_name, method_or_function_name, line_number = "", "", ""

        if execution_context:
            prefix += f"[{execution_context}]"
        if class_name:
            prefix += f"[{class_name}]"
        if method_or_function_name:
            prefix += f"[{method_or_function_name}"
            if self.log_line_number:
                prefix += f":{line_number}"
            prefix += f"]"
        if self.context_key.get():
            prefix += f"[{self.context_key.get()}]"

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