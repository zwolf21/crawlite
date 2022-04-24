from functools import reduce

from .core.parser.soup import SoupParser


from .actions import *









class RouteCrawler(CachedRequests):


    routers =[
        urlrender('https://kin.naver.com/search/list.naver', renderer='home_urlrenderer',  name='home')
    ]





    def reduce_parser(self, action, response):
        if parser := action.parser:
            results = parser(response)
            return results


    def reduce_urlfilter(self, action, url):
        if filter := action.urlfilter:
            return filter(url)
        return True
    

   

    def pipeline(self, name, result):
        return result
    
    def crawl(self, response=None):
        if not self.routers:
            return
        
        action = self.routers.pop(0)

        for url in self.reduce_url(action, response):
            if not self.reduce_urlfilter(action, url):
                continue

            r = self.reduce_response(action, url)

            self.inject_history(action, r)
            self.inject_pattern_group(action, r)
            self.inject_soup(r)
            self.inject_querydict(r)

            result =  self.reduce_parser(action, r)
            self.pipeline(action.name, result)

            self.crawl(r)
        

    

    
    

    

    



    


        



