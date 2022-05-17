import time

import requests_cache

from crawlite.utils.random import get_random_second
from crawlite.utils.module import FromSettingsMixin

from .utils import retry, set_user_agent
from .exceptions import *


class CachedRequests(FromSettingsMixin):
    HEADERS = None
    COOKIES = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {}
        self.cookies = {}
        self.headers = self.apply_settings(set_user_agent, header=self.headers)
        if self.HEADERS:
            self.headers.update(self.HEADERS)
        if self.COOKIES:
            self.cookies.update(self.COOKIES)

        self.requests = self.apply_settings(
            requests_cache.CachedSession,
            setting_prefix='REQUEST_CACHE_'
        )

    def get_request_log(self, url, from_cache, delay, payloads=None):
        if from_cache is False:
            if payloads is not None:
                log = f"POST {url} (delay:{delay}s, payloads:{payloads})"
            else:
                log = f"GET {url} (delay:{delay}s)"
        else:
            if payloads is not None:
                log = f"POST {url} From Cache (payloads:{payloads})"
            else:
                log = f"GET {url} From Cache"
        return log

    def _refresh_cache(self, url, method='get'):
        if method == 'get':
            if self.requests.cache.has_url(url):
                self.requests.cache.delete_url(url)
        else:
            self.requests.remove_expired_responses()

    def _delay_control(self, response):
        if response.from_cache is False:
            delay = self._get_delay()
            time.sleep(delay)
            return delay

    def _get_delay(self):
        if isinstance(self.REQUEST_DELAY, (tuple, list,)) and len(self.REQUEST_DELAY) == 2:
            return get_random_second(*self.REQUEST_DELAY)
        return self.REQUEST_DELAY

    def _validate_response(self, response):
        if not response.content:
            self.requests.cache.delete_url(response.url)
            raise ResponseHasNoContent(f'Warning: {response.url} has no content!')
    
    @retry
    def get(self, url, refresh, **kwargs):
        if refresh:
            self._refresh_cache(url)

        r = self.apply_settings(self.requests.get, url, **kwargs)
        r.raise_for_status()
        delay = self._delay_control(r)
        if self.REQUEST_LOGGING is True:
            log = self.get_request_log(url, r.from_cache, delay)
            print(log)
        self._validate_response(r)
        return r

    @retry
    def post(self, url, data, **kwargs):
        r = self.apply_settings(self.requests.post, url, data=data, **kwargs)
        r.raise_for_status()
        delay = self._delay_control(r)
        if self.REQUEST_LOGGING is True:
            log = self.get_request_log(url, r.from_cache, delay, len(data))
            print(log)
        return r

    def get_headers(self):
        return dict(self.headers)

    def set_header(self, headers):
        self.headers = headers
    
    def get_cookies(self):
        return dict(self.cookies)
    
    def set_cookies(self, cookies):
        self.cookies = cookies