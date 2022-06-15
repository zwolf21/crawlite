import shlex, re, argparse, functools




def parse_curl(command):
    tokens = shlex.split(command)
    return list(filter(None, map(str.strip, tokens)))
    

def create_parser(tokens):
    parser = argparse.ArgumentParser()
    parser.add_argument('appname')
    parser.add_argument('url')
    parser.add_argument('-X', '--method',)
    parser.add_argument('-H', '--headers', action='append', default=[])
    parser.add_argument('-d', '--data', '--data-binary', '--data-raw', '--data-urlencode', '--form', default=None)
    parser.add_argument('--connect-timeout')
    parser.add_argument('-k','--insecure', action='store_true', default=True)
    parser.add_argument('--compressed', action='store_true')
    return parser


def process_args(parser, tokens):
    def _parse(pat, v):
        if g:= pat.search(v):
            return {g.group('key'): g.group('value')}
        return {}

    def _parse_headers(h):
        pat = re.compile(r'(?P<key>.+?)\:\s*(?P<value>.+)')
        return _parse(pat, h)

    def _parse_cookies(c):
        pat = re.compile(r'(?P<key>.+?)=(?P<value>.+)')
        return _parse(pat, c)

    args = parser.parse_args(tokens)
    headers = functools.reduce(lambda acc, cur: acc | _parse_headers(cur), args.headers, {})

    if cookies := headers.get('cookie'):
        headers.pop('cookie')
        cookies = cookies.split(';')
        cookies=functools.reduce(lambda acc, cur: acc | _parse_cookies(cur), cookies, {})

    return dict(
        data=args.data,
        url=args.url,
        method=args.method or ('post' if  args.data else 'get'),
        timeout=args.connect_timeout,
        headers=functools.reduce(lambda acc, cur: acc | _parse_headers(cur), args.headers, {}),
        cookies=cookies,
        verify=args.insecure,
    )


def curl2requests(curl):
    tokens = parse_curl(curl)
    parser = create_parser(tokens)
    kwargs = process_args(parser, tokens)
    return kwargs