import time
import functools
from collections import abc

from fake_useragent import FakeUserAgent

from .exceptions import RetryMaxCountDone

def retry(func):
    @functools.wraps(func)
    def wrapper(self, url, **kwargs):
        if isinstance(self.RETRY_INTERVAL_SECONDS, abc.Iterable):
            for i, sec in enumerate(self.RETRY_INTERVAL_SECONDS):
                try:
                    r = func(self, url, **kwargs)
                except Exception as e:
                    print('exception', e)
                    err = f"Request {url} Failed, retry after {sec}sec(trys: {i+1})"
                    print(err)
                    time.sleep(sec)
                else:
                    return r
            else:
                raise RetryMaxCountDone(f'Request {url} Failed!')
        else:
            r = func(self, **kwargs)
        return r
    return wrapper


def set_user_agent(header, user_agent_name):
    header = header or {}
    fagent = FakeUserAgent()
    header['User-Agent'] = getattr(fagent, user_agent_name)
    return header
    