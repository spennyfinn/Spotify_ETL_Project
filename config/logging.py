import logging
import logging.handlers
from pathlib import Path

#Creates the logs directory and prevents errs if it exists
Path('logs').mkdir(exist_ok=True)

#Sets up the root logger, logs messages INFO level and above, sets the template, and timestamp format
logging.basicConfig(
    level=logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt= '%Y-%m-%d %H:%M:%S'
)

error_logger = logging.getLogger('database_errors')
error_logger.setLevel(logging.ERROR)
error_logger.propagate = False

file_handler = logging.handlers.TimedRotatingFileHandler( 'logs/database_errors.log', when='midnight', interval=1, backupCount=30)
file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s\n'
    'Module: %(module)s | Function: %(funcName)s | Line : %(lineno)d\n'
    'Extra: %(extra)s\n'
    '---\n',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
error_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
error_logger.addHandler(console_handler)