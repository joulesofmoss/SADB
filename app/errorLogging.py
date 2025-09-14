import logging
import sys
import traceback
import functools
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
import os

class PygramLogger: # logging shit!
    instance = None # public instance
    initialized = False # public initialized

    def new(cls):
        if cls.instance is None:
            cls.instance = super(pygramLogger, cls).__new__(cls)
        return cls.instance
    
    def init(self):
        if not self.initialized:
            self.setup_logging()
            pygramLogger.initialized = True
    
    def setup_logging(self):
        logDir = Path("logs")
        logDir.mkdir(exist_ok=True)
        timeStamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logFile = logDir / f"pygram{timeStamp}.log"
        self.logger = logging.getLogger("pygram")
        self.logger.setLevel(logging.DEBUG)

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        fileHandler = logging.FileHandler(logFile, encoding='UTF-8')
        fileHandler.setLevel(logging.DEBUG)
        
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )

        fileHandler.setFormatter(formatter)
        consoleHandler.setFormatter(formatter)
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)

        self.logger.info("=" * 50)
        self.logger.info("Pygram Application Started")
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"Log file: {logFile}")
        self.logger.info("=" * 50)

    def getLogger(self, name=None):
        if name:
            return logging.getLogger(f"pygram.{name}")
        return self.logger
pygramLogger = PygramLogger()

def getLogger(name=None):
    return pygramLogger.getLogger(name)
def logException(logger, exception, context=""):
    logger.error(f"Exception occured {context}: {str(exception)}")
    logger.error(f"Exception type: {type(exception).__name__}")
    logger.error(f"Trackeback:\n{traceback.format_exc()}")

def showErrorDialog(title, message, details=None):
    try:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if details:
            msg_box.setDetailedText(details)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    except Exception as e:
        print(f"Error Dialog Failed: {e}")
        print(f"Original Error - {title}: {message}")
        if details: print(f"Details: {details}")
def handleCritError(logger, exception, context="", showDialog=True):
    errorMsg = f"Critical error in {context}: {str(exception)}"
    logger.critical(errorMsg)
    logException(logger, exception, context)
    if showDialog:
        showErrorDialog(
            "Critical Error!",
            f"A critical error occured: {str(exception)}!\n\nContext: {context}\n\nCheck the log file for detailed information...",
        )
class erorrHandler:
    def __init__(self, operationName, logger=None, showUserError=True, Critical=False):
        self.operationName = operationName
        self.logger = logger or getLogger("error_handler")
        self.showUserError = showUserError
        self.Critical = Critical
    
    def __enter__(self):
        self.logger.debug(f"Starting operation: {self.operationName}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.Critical:
                handleCritError(self.logger, exc_val, self.operationName, self.showUserError)
            else:
                self.logger.error(f"Erorr in {self.operationName}: {str(exc_val)}")
                logException(self.logger, exc_val, self.operationName)

                if self.showUserError:
                    showErrorDialog(
                        "Operation Failed!",
                        f"Failed to {self.operationName.lower()}: {str(exc_val)}",
                        "Check the log file for more information...",
                    )
            
            return not self.Critical
        
        self.logger.debug(f"Successfully completed operation: {self.operationName}")

def safe_execute(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = getLogger(func.__module__)
        try:
            logger.debug(f"Executing {func.__name__} with args: {args[:2]}...")
            result = func(*args, **kwargs)
            logger.debug(f"Successfully executed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}"),
            logException(logger, e, f"function {func.__name__}"),
            raise
    return wrapper

def gui_safe_execute(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = getLogger(func.__module__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"GUI Error in {func.__name__}: {str(e)}"),
            logException(logger, e, f"GUI function {func.__name__}"),

            showErrorDialog(
                "Application error",
                f"An error occured while {func.__name__.replace('_', '')}: {str(e)}",
                "Please check the log file for more details!",
            )
            return None
    return wrapper

class FileOperationHandler:
    def __init__(self, operation, file_path=None):
        self.operation = operation
        self.file_path = file_path
        self.logger = getLogger("file_ops")

    def __enter__(self):
        self.logger.info(f"Starting file: {self.operation} on {self.file_path}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_msg = f"File operation failed - {self.operation}"
            if self.file_path:
                error_msg += f" on {self.file_path}"#
            
            self.logger.error(f"{error_msg}: {str(exc_val)}")
            logException(self.logger, exc_val, f"file operation {self.operation}")

            if isinstance(exc_val, FileNotFoundError):
                user_msg = f"File not found: {self.file_path}"
            elif isinstance(exc_val, PermissionError):
                user_msg = f"Permission denied accessing: {self.file_path}"
            elif isinstance(exc_val, OSError):
                user_msg = f"System error accessing file: {str(exc_val)}"
            else:
                user_msg = f"Failed to {self.operation.lower()}: {str(exc_val)}"
            
            showErrorDialog(
                f"file Operation Error!",
                user_msg,
                f"Operation: {self.operation}\nFile: {self.file_path}",
            )
            return True
        self.logger.info(f"Successfully completed file operation: {self.operation}!")

def setup_global_exception_handler():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = getLogger("global")
        logger.critical("Unhandled exception occured!")
        logger.critical(f"Exception type: {exc_type.__name__}")
        logger.critical(f"Exception value: {str(exc_value)}")
        logger.critical("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        try:
            showErrorDialog(
                "Unhandled Error!",
                f"An unexpected error occured: {str(exc_value)}",
                "The application may need to be restarted. Check the log file for details!",
            )
        except:
            pass
    sys.excepthook = handle_exception

class PerformanceMonitor:
    def __init__(self, operationName, logger=None):
        self.operationName = operationName
        self.logger = logger or getLogger("performance")
        self.startTime = None
    def enter(self):
        self.startTime = datetime.now()
        self.logger.debug(f"Performance monitoring started for: {self.operationName}")
        return self
    def exit(self, exc_type, exc_val, exc_tb):
        endTime = datetime.now()
        duration = (endTime - self.startTime).total_seconds()
        if duration > 1.0:
            self.logger.warning(f"Slow operation detected; {self.operationName}: {duration:.2f}s")
        else:
            self.logger.debug(f"Operation completed; {self.operationName}: {duration:.3f}s")

def validate_file_path(file_path, operation="access"):
    logger = getLogger("validation")

    if not file_path:
        logger.error(f"Empty file path provided for {operation}")
        raise ValueError("File path cannot be empty")
    path_obj = Path(file_path)

    if operation == "read" and not path_obj.exists():
        logger.error(f"File does not exist for reading: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if operation == "write":
        parent_dir = path_obj.parent
        if not parent_dir.exists():
            logger.info(f"Creating directory for write operation: {parent_dir}")
            parent_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(parent_dir, os.W_OK):
            logger.error(f"No write permission for directory: {parent_dir}")
            raise PermissionError(f"Cannot write to directory: {parent_dir}")
        logger.debug(f"File path validation successful: {file_path}")
        return True

#-- EXAMPLES FOR ADDING --
def wrap_existing_functions():
    logger = getLogger("wrapper")
    logger.info("Applying error handling wrappers to existing functions")

def initialize_error_handling():
    logger = getLogger("init")
    logger.info("Initializing error handling system...")
    setup_global_exception_handler()
    logger.info(f"Error handling system initialized successfully")
    logger.info(f"Log files will be saved to: {Path('logs').absolute()}")
    return logger

def setup_qt_error_handing(app):
    logger = getLogger("qt")

    def qt_message_handler(mode, context, message):
        if mode == 0:
            logger.debug(f"Qt Debug: {message}")
        elif mode == 1:
            logger.warning(f"Qt Warning: {message}")
        elif mode == 2:
            logger.error(f"Qt Critical: {message}")
        elif mode == 3:
            logger.critical(f"Qt Fatal: {message}")
    logger.info("Qt error handling configured")