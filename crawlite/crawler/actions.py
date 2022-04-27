from ..utils.regex import strcompile


class BaseAction:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        if not self.name:
            raise NotImplementedError(
                f"action name must be specified"
            )

    def as_kwargs(self):
        return self.__dict__




class UrlRenderAction(BaseAction):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not (self.host or self.urlrenderer):
            raise NotImplementedError(
                f"host or urlrenderer must be specified"
            )

    

class UrlPatternAction(BaseAction):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not (self.urlpattern or self.urlpattern_renderer):
            raise NotImplementedError(
                f"urlpattern or urlpattern_renderer must be specified"
            )
       
    def set_urlpattern(self, urlpattern_renderer, **kwargs):
        pattern = urlpattern_renderer(**kwargs)
        return strcompile(pattern)



def urlrender(
    host=None, urlrenderer=None,
    payloader=None, parser=None, extractor=None, urlfilter=None, breaker=None, fields=None, contentfile=False, referer=None, name=None, refresh=False):
    return UrlRenderAction(**locals())


def urlpattern(
    urlpattern=None, urlpattern_renderer=None, remove_duplicates=True, attrs=None, css_selector=None, recursive=False,
    payloader=None, parser=None, extractor=None, urlfilter=None, breaker=None, fields=None, contentfile=False, referer=None, name=None, refresh=False):
    return UrlPatternAction(**locals())




