import re

from bs4.element import Tag

def strcompile(exp):
    if isinstance(exp, str):
        return re.compile(exp)
    if isinstance(exp, re.Pattern):
        return exp


def extgroup(exp, target, asdict=False):

    if isinstance(target, Tag):
        target = target.get_text()

    regex = strcompile(exp)
    if g := regex.search(target):
        if asdict:
            return g.groupdict()
        return g.group

