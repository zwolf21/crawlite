import json, re
from functools import wraps
from itertools import dropwhile
from datetime import datetime


from bs4.element import Tag
from dateutil.relativedelta import relativedelta

def prettify_content(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        content = func(*args, **kwargs)

        if isinstance(content, Tag):
            content = content.get_text()

        if not content:
            return content

        trantab = {
            '<br>': '',
            '</br>': '\n',
            '<p>':'',
            '</p>': '\n',
            '\t': '',
            '\u200b': '',
            '\xa0': '',
            
        }
        for tok, repl in trantab.items():
            content = content.replace(tok, repl)
        
        lines = []
        for line in content.split('\n'):
            if line := line.strip():
                lines.append(line)

        return '\n'.join(lines)
    return wrapper



def extract_json(content, many=True):
    # vars,
    OPENING_BRAKET, CLOSING_BRAKET, OPENING_BRACE, CLOSING_BRACE = 'OPENING_BRAKET', 'CLOSING_BRAKET', 'OPENING_BRACE', 'CLOSING_BRACE',
    OPENING, CLOSING = 'OPENING', 'CLOSING',
    BRAKET, BRACE = 'BRAKET', 'BRACE',
    objmap = {
        '[': OPENING_BRAKET, b'[': OPENING_BRAKET,
        ']': CLOSING_BRAKET, b']': CLOSING_BRAKET,
        '{': OPENING_BRACE, b'{': OPENING_BRACE,
        '}': CLOSING_BRACE, b'}': CLOSING_BRACE,
    }

    balancer = {
        BRAKET: 0, BRACE:0
    }

    ## cut off head, tail impure
    content = ''.join(dropwhile(lambda c: objmap.get(c) not in [OPENING_BRAKET, OPENING_BRACE], content))
    content = ''.join(reversed(list(dropwhile(lambda c: objmap.get(c) not in [CLOSING_BRAKET, CLOSING_BRACE], reversed(content)))))


    _records = []
    for i, c in enumerate(content):
        if not(token := objmap.get(c)):
            continue

        option, kind = token.split('_') # ex) OPENING, BRACE

        if option == OPENING:
            balancer[kind] += 1
        else:
            balancer[kind] -= 1
        
        record = dict(
            index=i, kind=kind, option=option, balance=balancer[kind]
        )
        _records.append(record)
    
    if len(_records) < 2:
        return []

    starts = None
    tokens = []
    for r in _records:
        if starts is None:
            starts = r
            continue
        if starts['kind'] == r['kind'] and r['option'] == CLOSING and r['balance'] == 0:
            tok = content[starts['index']: r['index']+1]
            tokens.append(tok)
            starts = None

    success = []
    for tok in tokens:
        try:
            obj = json.loads(tok)
        except json.decoder.JSONDecodeError:
            continue
        success.append(obj)
    if many:
        return success
    else:
        if success:
            return success[0]
        

date_formats = {
    'fulldatetime': r'(?P<year>\d{2,4})[\.\-/???]\s*(?P<month>[0-2]?\d)[\.\-/???]\s*(?P<day>[0-3]?\d)[\.???]?[\sT]+(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[\:\s???]\s*(?P<second>[0-5]?\d)[???]?',
    'fulldatehourminute': r'(?P<year>\d{2,4})[\.\-/???]\s*(?P<month>[0-2]?\d)[\.\-/???]\s*(?P<day>[0-3]?\d)[\.???]?[\sT]+(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[???]?',
    'monthdayfulltime': r'(?P<month>[0-2]?\d)[\.\-/???]\s*(?P<day>[0-3]?\d)[\.???]?[\sT]+(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[\:\s???]\s*(?P<second>[0-5]?\d)[???]?',
    'monthdayhourminute': r'[\.]?(?P<month>[0-2]?\d)[\.\-/???]\s*(?P<day>[0-3]?\d)[\.???]?[\sT]+(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[???]?',
    'fulldate': r'(?P<year>\d{2,4})[\.\-/???]\s*(?P<month>[0-2]?\d)[\.\-/???]\s*(?P<day>\d{1,2})[\.???]?', #2022.2.3
    'monthday': r'[\.]?(?P<month>[0-2]?\d)[\.\-/???]\s*(?P<day>[0-3]?\d)[\.???]?', # 5.7, 1.2 .02.11, 
    'fulltime': r'(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[\:\s???]\s*(?P<second>[0-5]?\d)[???]?',
    'hourminute': r'(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[\:\s???]?',
    'timedelta_seconds': r'(?P<seconds>[0-5]?\d)\s*(?P<unit>???|second[s]?|sec)\s*(?P<ago>???|ago)',
    'timedelta_minutes': r'(?P<minutes>[0-5]?\d)\s*(?P<unit>???|minute[s]?|min)\s*(?P<ago>???|ago)',
    'timedelta_hours': r'(?P<hours>[0-5]?\d)\s*(?P<unit>??????|hour[s]?)\s*(?P<ago>???|ago)',
    'timedelta_days': r'(?P<days>\d{1,3})\s*(?P<unit>???|day[s]?)\s*(?P<ago>???|ago)',
    'timedelta_months': r'(?P<months>\d{1,2})\s*(?P<unit>???|month[s]?|??????)\s*(?P<ago>???|ago)',
    'timedelta_weeks': r'(?P<weeks>\d{1,2})\s*(?P<unit>???|week[s]?|??????)\s*(?P<ago>???|ago)',
    'timedelta_years': r'(?P<years>\d{1,2})\s*(?P<unit>???|year[s]?)\s*(?P<ago>???|ago)',
    'timedelta_now': r'(?P<now>??????\s*[???]?|now|??????)',
    'yesterday': r'(??????|?????????)\s*(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[\:\s???]?',
    'beforeyesterday': r'(??????|?????????|?????????)\s*(?P<hour>[0-5]?\d)[\:\s???]\s*(?P<minute>[0-5]?\d)[\:\s???]?',
}


def try2datetime(str_date):
    if isinstance(str_date, Tag):
        str_date = str_date.get_text()
    
    n = datetime.now()
    pm = re.search('??????|pm', str_date, re.IGNORECASE)
    str_date = re.sub('??????|pm|??????|am', '', str_date).strip()
        
    for type, pat in date_formats.items():
        pat = re.compile(pat)
        if g:= pat.search(str_date):
            if type.startswith('timedelta'):
                _, t = type.split('_')
                if t == 'now':
                    return n
                return n - relativedelta(**{t: int(g.group(t))})

            kw = {k: int(v) for k,v in g.groupdict().items()}

            if year := kw.get('year'):
                if year < 100:
                    if year + 2000 > n.year:
                        year = 1900 + year
                    else:
                        year = 2000 + year
                    kw['year'] = year
            else:
                kw['year'] = n.year

            if pm:
                if hour := kw.get('hour'):
                    kw['hour'] = hour + 12

            if type in ['fulldate', 'fulldatetime', 'fulldatehourminute']:
                return datetime(**kw)
            elif type in ['monthday', 'monthdayfulltime']:
                return datetime(**kw)
            if type in ['monthdayhourminute']:
                return datetime(second=0, **kw)
            if type in ['fulltime', 'hourminute']:
                return datetime(month=n.month, day=n.day, **kw)
            if type in ['yesterday']:
                return datetime(month=n.month, day=n.day, **kw) - relativedelta(days=1)
            if type in ['beforeyesterday']:
                return datetime(month=n.month, day=n.day, **kw) - relativedelta(days=2)

    raise ValueError('Cannot find datepattern in %s' % str_date)
