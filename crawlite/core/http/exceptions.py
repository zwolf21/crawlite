class RequestErrorBase(Exception):
    '''Request Exception Base
    '''


class RetryMaxCountDone(RequestErrorBase):
    '''Retry maximum count over
    '''


class ResponseHasNoContent(RequestErrorBase):
    '''Response has no contents
    '''


class RotateProxiesDone(RequestErrorBase):
    '''Rotate all Proxies list
    '''