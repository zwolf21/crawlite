import requests_cache

from crawlite.utils.etc import get_random_second, get_rotate
from crawlite.settings import FromSettingsMixin

from .utils import set_user_agent
from .exceptions import *
from .adapters import CrawliteFileAdapter
from .helper import trace, retry_for_raise, rotate_proxy
from .curl import curl2requests



class CachedRequests(FromSettingsMixin):
    HEADERS = None
    COOKIES = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {}
        self.cookies = {}
        self.proxies_list = []
        
        if self.HEADERS:
            self.headers.update(self.HEADERS)
        else:
            self.headers = self.apply_settings(
                set_user_agent, setting_prefix='FAKE_USER_AGENT_',
            )

        if self.COOKIES:
            self.cookies.update(self.COOKIES)

        if hasattr(self, 'PROXIES_LIST'):
            self.proxies_list = self.PROXIES_LIST
        
        self.requests = self.apply_settings(
            requests_cache.CachedSession,
            setting_prefix='REQUEST_CACHE_'
        )
        self.requests.mount('file:///', CrawliteFileAdapter())

    
    def get_delay(self, delay):
        return delay or get_random_second(*self.REQUEST_DELAY)   

    
    def delete_cache(self, **requests_kwargs):
        cachekey = self.requests.cache.create_key(**requests_kwargs)
        self.requests.cache.delete(cachekey)


    @trace
    @retry_for_raise
    @rotate_proxy
    def fetch(self, method, refresh, delay, proxies=None, logging=True, **kwargs):
        if refresh:
            self.delete_cache(method=method, **kwargs)

        proxies = proxies or self.get_proxies()
        if proxies not in self.proxies_list:
            self.proxies_list.insert(0, proxies)

        r = self.apply_settings(
            self.requests.request, setting_prefix='REQUESTS_', method=method, proxies=proxies, **kwargs
        )

        if r.status_code not in self.REQUEST_CACHE_ALLOWABLE_CODES:
            r.raise_for_status()
        return r
    
    def from_curl(self, command, refresh, delay, **kwargs):
        p = curl2requests(command)
        return self.fetch(
            p.pop('method'), refresh, delay, **kwargs, **p
        )
        

    def get_headers(self):
        return dict(self.headers)

    def set_header(self, headers):
        self.headers = headers
    
    def get_cookies(self):
        return dict(self.cookies)
    
    def set_cookies(self, cookies):
        self.cookies = cookies

    def get_proxies(self):
        for proxies in self.proxies_list:
            return proxies
        
    def rotate_proxies(self):
        if self.proxies_list:
            self.proxies_list = get_rotate(self.proxies_list)
            return self.proxies_list[0]
