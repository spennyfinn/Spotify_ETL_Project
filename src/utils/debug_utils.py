import logging
from src.utils.text_processing_utils import get_words_list
import multiprocessing

logger = logging.getLogger(__name__)

w=get_words_list()
logger.debug(f'Words list: {w}')
logger.debug(f'Index of "involve": {w.index("involve")}')


