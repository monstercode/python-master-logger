
import logging
import sys
import contextvars
import threading

from contextlib import contextmanager


class _ContextFilter(logging.Filter):
    """Inject execution context into every LogRecord."""

    def __init__(self, process_context, context_key, log_line_number=True):
        super().__init__()
        self.process_context = process_context
        self.context_key = context_key
        self.log_line_number = log_line_number

    def filter(self, record):
        parts = []

        execution_context = self.process_context.get()
        context_key = self.context_key.get()

        class_name = getattr(record, "_app_class_name", "")

        if execution_context:
            parts.append(execution_context)

        if class_name:
            parts.append(class_name)

        method = record.funcName

        if method:
            if self.log_line_number:
                parts.append(f"{method}:{record.lineno}")
            else:
                parts.append(method)

        if context_key:
            parts.append(context_key)

        record.context_prefix = "".join(
            f"[{part}]" for part in parts
        )

        return True


class Logger:
    """Application-level singleton logger.

    Supports:
        - Thread-safe singleton initialization.
        - Context-local execution metadata using ContextVar.
        - Automatic caller identification.
        - Nested context managers.
        - Standard Python logging formatting and exception handling.

    Log format:
        [datetime][level][execution][class][method:line][context_key] message
    """

    _instance = None
    _instance_lock = threading.Lock()
    _init_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(
        self,
        log_line_number=True,
        logger_level=logging.DEBUG
    ):
        # Protect initialization from concurrent calls.
        with self._init_lock:

            if getattr(self, "_initialized", False):
                return

            self.process_context = contextvars.ContextVar(
                "logger_exec_context",
                default=""
            )

            self.context_key = contextvars.ContextVar(
                "logger_context_key",
                default=""
            )

            self.log_line_number = log_line_number

            self.logger = logging.getLogger("master-logger")
            self.logger.setLevel(logger_level)

            # Avoid adding duplicate filters.
            self.logger.addFilter(
                _ContextFilter(
                    self.process_context,
                    self.context_key,
                    log_line_number
                )
            )

            # Do not configure the global root logger here.
            # Logging handlers and formatters belong to the application.

            self._initialized = True

    # ---------------------------------------------------------
    # Context management
    # ---------------------------------------------------------

    def set_context_key(self, context_key: str):
        """Set the current context key."""

        return self.context_key.set(context_key)

    def set_process_context(self, execution_context: str):
        """Set the current execution context."""

        return self.process_context.set(execution_context)

    def get_process_context(self) -> str:
        return self.process_context.get()

    def get_context_key(self) -> str:
        return self.context_key.get()

    @contextmanager
    def context(self, execution=None, key=None):
        """Temporarily set execution context and context key.

        Previous values are restored automatically, supporting
        nested contexts and exceptions.
        """

        execution_token = None
        key_token = None

        try:
            if execution is not None:
                execution_token = self.process_context.set(execution)

            if key is not None:
                key_token = self.context_key.set(key)

            yield self

        finally:
            if key_token is not None:
                self.context_key.reset(key_token)

            if execution_token is not None:
                self.process_context.reset(execution_token)

    # ---------------------------------------------------------
    # Caller identification
    # ---------------------------------------------------------

    def _get_caller_class(self) -> str:
        """Identify the class calling the logger.

        Uses the calling frame instead of inspecting the entire stack.
        """

        try:
            caller_frame = sys._getframe(2)

            if "self" in caller_frame.f_locals:
                return caller_frame.f_locals["self"].__class__.__name__

            if "cls" in caller_frame.f_locals:
                return caller_frame.f_locals["cls"].__name__

            return ""

        except (ValueError, AttributeError):
            return ""

    # ---------------------------------------------------------
    # Internal logging
    # ---------------------------------------------------------

    def _log(self, level, message, *args, **kwargs):

        # Avoid unnecessary work when the log level is disabled.
        if not self.logger.isEnabledFor(level):
            return

        class_name = self._get_caller_class()

        # Prevent callers from accidentally overriding our stacklevel.
        kwargs.pop("stacklevel", None)

        self.logger.log(
            level,
            message,
            *args,
            extra={
                "_app_class_name": class_name
            },
            stacklevel=3,
            **kwargs
        )

    # ---------------------------------------------------------
    # Public logging methods
    # ---------------------------------------------------------

    def debug(self, message, *args, **kwargs):
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self._log(logging.CRITICAL, message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        """Log an exception with its traceback."""

        kwargs.setdefault("exc_info", True)

        self._log(logging.ERROR, message, *args, **kwargs)
