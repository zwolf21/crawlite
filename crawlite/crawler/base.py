from collections import abc, deque
import time
from urllib.error import URLError


from ..core.http.cached_request import CachedRequests
from ..core.parser.soup import SoupParser
from ..utils.urls import queryjoin, urljoin
from ..utils.module import find_function, filter_kwargs
from ..settings import CRAWL_SUSPENDE_LOOP_POLLING_RATE
from .exceptions import *
from .actions import UrlPatternAction, UrlRenderAction
from .reducer import ReducerMixin
from .meta import ResponseMeta
from .event import CRAWLING_STARTED, CRAWLING_COMPLETED, VISITING_URL, CRAWLING_STOPPED, CRAWLING_SUSPENDED, catch_crawl_exception




class BaseCrawler(CachedRequests, SoupParser, ReducerMixin):
    urlorders = None

    
    def __init__(self, *args, crawl_listener=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_listener = crawl_listener or (lambda module, event, context: True)


    def _resolve_link(self, link, action, response=None):
        if isinstance(action, UrlRenderAction): 
            host = action.host or response.url
        else:
            host = response.url
        if isinstance(link, abc.Mapping):
            return queryjoin(host, link)
        return urljoin(host, link)


    def _dispatch_renderer(self, action, response, responsemap, context):
        
        if isinstance(action, UrlRenderAction):
            if urlrenderer := action.urlrenderer:
                links = self.dispatch(
                    'urlrenderer', urlrenderer,
                    url=action.host, parent_response=response, responsemap=responsemap, context=context
                )                
                if links is None:
                    raise UrlRendererError(f"{urlrenderer} must return or yield url, link or params, not {links}")
            elif host := action.host:
                links = [host]
            else:
                raise URLError("urlrender: host or renderer must be specified!")
        elif isinstance(action, UrlPatternAction):
            if urlpattern_renderer := action.urlpattern_renderer:
                urlpattern = self.dispatch(
                    'urlpattern_renderer', urlpattern_renderer,
                    pattern=action.urlpattern, parent_response=response, responsemap=responsemap, context=context
                )
                if urlpattern is None:
                    raise UrlRendererError(f"{urlpattern_renderer} must return regex pattern of url, not {urlpattern}")
            else:
                urlpattern = action.urlpattern
            # action.urlpattern 의 원본 유지를 위해
            kwargs = {
                **action.as_kwargs(),
                'urlpattern': urlpattern
            }
            links = self.parse_linkpattern(response.content, **kwargs)
        return links      


    def _dispatch_extractor(self, action, meta, context):
        extractset = {}
        if module := action.extractor:
            pat = r'^extract_(?P<ext>\w+)$'
            for g, func in find_function(module, pat):
                extracted = filter_kwargs(func, meta=meta, soup=meta.soup, context=context)
                extractset[g('ext')] = self.validate_extracted(extracted, func, meta)
        return extractset


    def _dispatch_parser(self, action, response, extracted, meta, context):
        results = self.dispatch(
            'parser', action.parser,
            response=response, parsed=extracted, meta=meta, context=context
        )
        return results


    def _dispatch_urlfilter(self, action, url, responsemap, context):
        return self.dispatch(
            'urlfilter', action.urlfilter,
            url=url, responsemap=responsemap,  context=context
        )
    
    
    def _dispatch_payloader(self, action, context):
        if not action.payloader:
            yield None
        payloads = self.dispatch('payloader', action.payloader, context=context)
        if isinstance(payloads, (str, bytes)):
            yield payloads
        else:
            yield from payloads
        
    def _dispatch_response(self, action, url, headers, payload=None):
        if payload:
            response = self.post(url, payload=payload, headers=headers, **action.as_kwargs())
        else:
            response = self.get(url, headers=headers, **action.as_kwargs())
        return response



    def _dispatch_referer(self, action, response):
        header = self.get_header()
        if action.referer and response:
            try:
                referer = response.crawler.responsemap[action.referer]
            except KeyError:
                raise CannotFindAction(f"An action named {action.referer} could not be found at urlorders.")
            else:
                header['Referer'] = referer.url
        return header
    
    
    def _dispatch_breaker(self, action, response, context):
        return self.dispatch(
            'breaker', action.breaker, response, context=context
        )
    

    def get_action(self, name):
        for action in self.urlorders:
            if action.name == name:
                return action

    def pipeline(self, results, action):
        return results


    @catch_crawl_exception
    def crawl(self, context=None, _response=None, _urlorders=None, _visited=None, _responsemap=None, _visite_count=0):

        module_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        action, *rest = _urlorders or self.urlorders

        response_queue = deque([_response])
        _visited = _visited or set()
        
        if _response is None:
            self.crawl_listener(module_name, CRAWLING_STARTED, {'visite_count': _visite_count})

        while response_queue:
            response = response_queue.pop()

            is_parsable = True
            for link in self._dispatch_renderer(action, response, _responsemap, context):
                url = self._resolve_link(link, action, response)

                if not self._dispatch_urlfilter(action, url, _responsemap, context):
                    continue

                if url in _visited:
                    continue
                    
                if isinstance(action, UrlPatternAction):
                    _visited.add(url)

                ## listen visiting url
                _visite_count += 1
                self.crawl_listener(module_name, VISITING_URL, {'visite_count': _visite_count})
                
                ## listen breaking loop
                if self._dispatch_breaker(action, response, context) is True:
                    self.crawl_listener(module_name, CRAWLING_STOPPED, {'visite_count': _visite_count})
                    return

                header_referer = self._dispatch_referer(action, response)
                
                #check post method
                for payload in self._dispatch_payloader(action, context):
                    if payload:
                        sub_response = self._dispatch_response(action, url, header_referer, payload)
                    else:
                        sub_response = self._dispatch_response(action, url, header_referer)  

                    ## content type check
                    is_parsable = self._is_parsable(sub_response)
                    soup = self._load_soup(sub_response.content) if is_parsable else None

                    ## respone meta setting
                    meta = ResponseMeta(soup=soup)
                    meta.set_urlutils(link, action)
                    meta.set_responsemap(response, action)

                    if response:
                        meta.update_responsemap(response.crawler.responsemap)
                    setattr(sub_response, 'crawler', meta)

                    if _responsemap:
                        meta.update_responsemap(_responsemap)

                    ## parsing
                    extracted = self._dispatch_extractor(action, meta, context)
                    results = self._dispatch_parser(action, sub_response, extracted, meta, context)
                    self.pipeline(results, action)

                    if is_parsable is True:
                        if isinstance(action, UrlPatternAction):
                            if action.recursive:
                                response_queue.append(sub_response)
                        if rest: self.crawl(context, sub_response, rest, _visited, meta.responsemap, _visite_count)

            # BFO if not passable
            if is_parsable is False:
                if rest: self.crawl(context, response, rest, _visited, meta.responsemap, _visite_count)
        
        if _response is None:
            self.crawl_listener(module_name, CRAWLING_COMPLETED, {'visite_count': _visite_count})
