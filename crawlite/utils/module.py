import inspect
from itertools import takewhile

from .regex import strcompile



def find_function(module, regex):
    if not inspect.ismodule(module):
        raise ValueError(f"{module} is Not python module  .py")
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if g := strcompile(regex).search(name):
            yield g.group, func


def module2dict(module):
    return dict(takewhile(lambda i: i[0] != '__builtins__', inspect.getmembers(module)))


# selectable kwargs
def filter_kwargs(callable, *args, **kwargs):
    sig = inspect.signature(callable)
    kw = {}
    for k, v in kwargs.items():
        if k in sig.parameters:
            kw[k] = v
    return callable(*args, **kw)




