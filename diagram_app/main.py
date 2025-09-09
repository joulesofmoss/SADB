import sys
from PyQt6.QtWidgets import QApplication
from ui.diagram_editor import DiagramEditor
from errorLogging import (getLogger, erorrHandler, FileOperationHandler, gui_safe_execute, safe_execute, PerformanceMonitor, validate_file_path, initialize_error_handling)
from errorLogging import initialize_error_handling, setup_qt_error_handing

@safe_execute
def main():
    logger = initialize_error_handling()
    logger.info("Starting Pygram application")
    try:
        app = QApplication(sys.argv)
        setup_qt_error_handing(app)
        with erorrHandler("application setup", Critical=True):
            window = DiagramEditor()
            window.show()
        logger.info("Application GUI initialized successfully")
        result = app.exec()
        logger.info(f"Application exited with code: {result}")
        return result
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())