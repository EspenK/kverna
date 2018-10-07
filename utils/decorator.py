import logging
import functools
import inspect
import datetime


log = logging.getLogger("discord")


def logger(func):
    """Decorator to log function name and arguments when called, and log it's result.

    :param func: The function to decorate.
    :return: The wrapped function.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            log.debug(f'{func.__name__} called with args {args}, kwargs {kwargs}')
            result = await func(*args, **kwargs)
            log.debug(f'{func.__name__} returns {result}')
            return result
    else:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            log.debug(f'{func.__name__} called with args {args}, kwargs {kwargs}')
            result = func(*args, **kwargs)
            log.debug(f'{func.__name__} returns {result}')
            return result
    return wrapped


def timeit(func):
    """Decorator to log function name execution time.

    :param func: The function to decorate.
    :return: The wrapped function.
    """
    if inspect.iscoroutinefunction(func):
        async def wrapped(*args, **kwargs):
            start_time = datetime.datetime.now()
            result = await func(*args, **kwargs)
            end_time = datetime.datetime.now()
            delta = end_time - start_time
            log.debug(f'{func.__name__} executed in {delta.total_seconds() * 1000:.2f} milliseconds')
            return result
    else:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            start_time = datetime.datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.datetime.now()
            delta = end_time - start_time
            log.debug(f'{func.__name__} executed in {delta.total_seconds() * 1000:.2f} milliseconds')
            return result
    return wrapped
