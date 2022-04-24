from functools import wraps
import re

def prettify_content(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        content = func(*args, **kwargs)
        if not content:
            return content
            
        trantab = {
            '<br>': '',
            '</br>': '\n',
            '<p>':'',
            '</p>': '\n',
            '\t': '',
            '\u200b': ''
        }
        for tok, repl in trantab.items():
            content = content.replace(tok, repl)
        
        lines = []
        for line in content.split('\n'):
            if line := line.strip():
                lines.append(line)

        return '\n'.join(lines)
    return wrapper