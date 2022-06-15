import functools, time
from collections import abc

from requests.exceptions import ProxyError, ConnectTimeout

from .exceptions import RetryMaxCountDone, RotateProxiesDone
from crawlite.utils.etc import transform_bytes_length




def _get_pre_request_log(method, url, data=None, proxies=None, **extra):
    METHOD = method.upper()
    PROXIES = f"proxy:{proxies}" if proxies else '' 
    prefix = ' '.join(filter(None, [METHOD, url, PROXIES]))
    PAYLOADS = f"payloads:{transform_bytes_length(payloads, 2)}" if (data:=data) and (payloads := len(data)) else ''
    
    if postfix:= list(filter(None, [PAYLOADS])):
        postfix = ', '.join(postfix)
        postfix = f' ({postfix})'
    else:
        postfix = ''

    log = f"{prefix}{postfix}"
    return log



def _get_after_request_log(response, delay):
    content_length = len(response.content or '')
    status = response.status_code
    reason = response.reason
    size_exp = transform_bytes_length(content_length)
    elapsed = round(response.elapsed.microseconds / (1000 * 1000),2)

    log = f'{status} {reason}  {size_exp} {elapsed}s'

    if ctype:= response.headers.get('Content-Type'):
        log = f'{log} {ctype}'

    if response.from_cache:
        log = f'{log} (From Cache)'
    else:
        log = f'{log} (delay:{delay or 0}s)'
    return log



def trace(func):
    @functools.wraps(func)
    def wrapper(self, method, refresh, delay,**kwargs):
        try:
            proxies = self.get_proxies()
            pre_log = _get_pre_request_log(method, proxies=proxies, **kwargs)
            print(f'{pre_log}')
            r = func(self, method, refresh, delay, **kwargs)
            log = f'  => {_get_after_request_log(r, delay)}'
            print(log)
            if not r.from_cache:
                time.sleep(delay)
        except Exception as e:
            print(e)
            raise
        else:
            return r
    return wrapper



def retry_for_raise(fetch):
    @functools.wraps(fetch)
    def wrapper(self, *args, **kwargs):
        url = kwargs.get('url')
        retry_intervals = list(self.RETRY_INTERVAL_SECONDS)
        while retry_intervals:
            try:
                response = fetch(self, *args, **kwargs)
            except Exception as e:
                if self.proxies_list and isinstance(e, RotateProxiesDone):
                    raise
                interval = retry_intervals.pop(0)
                print(f" - {e}")
                print(f" - Request {url} Failed, retry after {interval} sec...(retry remains: {len(retry_intervals)})")
                time.sleep(interval)
            else:
                return response
        raise RetryMaxCountDone(f"Request for {url} has failed!")
    return wrapper



def rotate_proxy(fetch):
    @functools.wraps(fetch)
    def wrapper(self, *args, **kwargs):
        if not self.proxies_list:
            return fetch(self, *args, **kwargs)
        init_proxy = self.get_proxies()
        next_proxy = {}
        rotate_count = 0
        while True:
            try:
                response = fetch(self, *args, **kwargs)
            except (ProxyError, ConnectTimeout) as e:
                if init_proxy != next_proxy:
                    break
                print(e)
                rotate_count += 1
                current_proxy = self.get_proxies()
                next_proxy = self.rotate_proxies()
                print(f" - The requests by pass proxy server {current_proxy} has failed. Trying to next proxy server {next_proxy}...(rotate rate: {rotate_count}/{len(self.proxies_list)})")
            else:
                return response
        raise RotateProxiesDone(f"All requests through {len(self.proxies_list)} proxies fail")
    return wrapper


