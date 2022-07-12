from fake_useragent import FakeUserAgent



def set_user_agent(header=None, user_agent_name='chrome', **fkagent_kwargs):
    header = header or {}
    fagent = FakeUserAgent(**fkagent_kwargs)
    header['User-Agent'] = getattr(fagent, user_agent_name)
    return header
