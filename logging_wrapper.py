import functools
import logging


def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger()
            logger.exception(f"Exception raised in {func.__name__}. exception: {str(e)}")
            raise

    return wrapper
