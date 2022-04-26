import functools


CRAWLING_STARTED = 'CRAWINGL_STARTED'
CRAWLING_COMPLETED = 'CRAWLING_COMPLETED'
CRAWLING_STOPPED = 'CRAWLING_STOPPED'
CRAWLING_SUSPENDED = 'CRAWLING_SUSPENDED'
VISITING_URL = 'VISITING_URL'
EXCEPTION_OCCURED = 'EXCEPTION_OCCURED'



def catch_crawl_exception(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            r = func(self, *args, **kwargs)
        except Exception as e:
            module_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
            crawl_listener = kwargs.get('crawl_listener')
            crawl_listener(module_name, EXCEPTION_OCCURED, {'exception': e})
        else:
            return r
    return wrapper

