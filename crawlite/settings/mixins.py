import inspect
from collections import abc

from . import default
from ..utils.module import module2dict




class FromSettingsMixin:

    def __init__(self, settings=None):
        defaults = module2dict(default)
        if settings:
            if isinstance(settings, abc.Mapping):
                customs = settings
            else:
                customs = module2dict(settings)
            defaults.update(customs)
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        self._validate_retry_interval_seconds()
        self._validate_request_delay()


    def _validate_retry_interval_seconds(self):
        value = self.RETRY_INTERVAL_SECONDS
        if value is None:
            value = ()

        if isinstance(value, (int, float)):
            value = value, 
        
        if not isinstance(value, (tuple, list)):
            raise ValueError('RETRY_INTERVAL_SECONDS must be tuple of numbers or a number')
        self.RETRY_INTERVAL_SECONDS = value


    def _validate_request_delay(self):
        value = self.REQUEST_DELAY
        if not value:
            value = 0, 0
        elif isinstance(value, (int, float)):
            value = value, value,
        elif isinstance(value, (list, tuple)):
            if len(value) == 1:
                value = value[0], value[0]
            else:
                value = value[0], value[-1]
        else:
            raise ValueError('REQUEST_DELAY must be tuple of numbers or a number')
        self.REQUEST_DELAY = value
        

    def apply_settings(self, callable, *args, setting_prefix=None, lower_key=True, **kwargs):
        sig = inspect.signature(callable)
        kw = {**self.__dict__}

        if setting_prefix:
            kw = {
                k.replace(setting_prefix, ''): v for k, v in kw.items()
                if k.startswith(setting_prefix)
            }
        if lower_key:
            kw = {
                k.lower(): v for k,v in kw.items()
            }
        if not setting_prefix:
            kw = {
                k: v for k, v in kw.items()
                if k in sig.parameters
            }
        kwargs = {
            **kwargs,
            **kw,
        }
        return callable(*args, **kwargs)
        
