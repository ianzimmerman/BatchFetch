import argparse
import csv
import json
import time
from datetime import datetime
from io import BytesIO
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import urlopen

import core.apis.config as config
import requests
from core.apis import AbstractQuery


class SERPStatQuery(AbstractQuery):
    def __init__(self, key=None):
        self.key = key or config.SERP_STAT_TOKEN

        self.query = None
        self.api_method = None
        self.se = None

        self.limit_requests = True
        self.rps = 1  #requests per second
        self.lr = datetime.now()  #last request
        
        self._filters = {
            'position_from': 1,
            'position_to': 20,
            'queries_from': 500,
            'right_spelling': 'not_contains'
        }
        
        self._sort_by = {
            'sort': 'traff',
            'order': 'desc'
        }
        self._pagination = {
            'page': 1,
            'page_size': 25
        }

        self._headers = [
            "keyword",
            "region_queries_count",
            "region_queries_count_wide",
            "position",
            "traff",
            "cost",
            "url",
            "domain",
            "subdomain",
            "keyword_length",
            "types",
            "found_results",
            "concurrency",
            "geo_names",
            "difficulty",
            "right_spelling",
            "dynamic",
            "_id"
        ]
        # if self.domain:
        #     self.add_filter('+', 'Ur', 'Co', self.domain)

        # self.set_columns()
    
    @property
    def headers(self):
        return self._headers

    def mod_filter(self, param, value):
        """
        Parameter	        Description	                        Possible settings
        position_from	    min position for a keyword	        1-100
        position_to	        max position for a keyword	        1-100
        queries_from	    min number of monthly searches	    0-100,000,000
        queries_to	        max number of monthly searches	    0-100,000,000
        cost_from	        min CPC	                            0-200
        cost_to	            max CPC	                            0-200
        concurrency_from	min level of competition	        1-100
        concurrency_to	    max level of competition	        1-100
        right_spelling	    filtering by misspelled keywords    not_contains - contains misspelled keywords;
                                                                contains - does not contain misspelled keywords
        """
        available_params = [
            'position_from',
            'position_to',
            'queries_from',
            'queries_to',
            'right_spelling',
        ]

        if param in available_params:
            self._filters[param] = value

        return self

    def _args(self):
        params = {
            'query': self.query,
            'se': self.se,
            'token': self.key,
        }

        for k, v in self._filters.items():
            params[k] = str(v)
        
        for k, v in self._sort_by.items():
            params[k] = str(v)
        
        for k, v in self._pagination.items():
            params[k] = str(v)

        return params

    def sleep_if_needed(self):
        if self.limit_requests:
            et = (datetime.now() - self.lr).total_seconds()
            if et < (1/self.rps):
                break_time = (1/self.rps) - et
                time.sleep(break_time)
    
    def request(self, query, limit=25, method='url_keywords', se='g_us'):
        """
        api.serpstat.com/v3/{API_method}?query={domain.com}&token={token}&se={se}
        """

        self.query = query
        self.api_method = method
        self.se = se

        self._pagination['page_size'] = min(limit, 1000)

        args = urlencode(self._args(), quote_via=quote)
        self.request_uri = f"{config.SERP_STAT_ENDPOINT}/{self.api_method}?{args}"
        
        self.sleep_if_needed() # api speed limits
        
        self.response = requests.get(self.request_uri)
        self.lr = datetime.now()

        return self
    
    @property
    def results(self):
        result = json.loads(self.response.text)
        if result.get('result'):
            return result['result']['hits']
        else:
            return []
            
    def _set_sort(self, metric, order='desc'):
        '''
        To sort the results apply following parameters:

        sort : field that needs to be sorted;
        order : sorting order (asc - ascending, desc -  descending).
        
        Metrics	                    Description
        result	                    Encapsulates the answer
        total	                    Number of keywords for which the page ranks in top-100
        region_queries_count	    Search volume in selected search engine database
        region_queries_count_wide	Search volume (broad match)
        domain	                    Domain
        keyword_length	            Number of words divided by space in a keyword
        keyword	                    Query for which an ad is displayed in SERP
        url	                        URL of a page which appears in SERP for the keyword
        dynamic	                    How the position of this keyword has changed
        traff	                    Approximate organic traffic prognosis
        keyword_crc	                the checksum for a quick search
        types	                    A list of special elements shown in SERP (for example, video, carousel or map)
        found_results	            The number of results found for ""keywords""
        url_crc	                    CRC code (encryption method)
        cost	                    Cost per click, $
        concurrency	                Keyword competition in PPC (0-100)
        position	                Position for a keyword
        keyword_id	                Keyword ID in our database
        subdomain	                Subdomain which ranks for the keyword
        types	                    A list of special elements shown in SERP (for example, video, carousel or map)
        geo_names	                List of toponyms in the array (if toponyms are present in the keywords)
        status_msg	                Response "OK" or "Error" report on a successful or unsuccessful request
        status_code	                Response code "200" — successful request. 

        Errors occur when limits are exceeded (number of simultaneous requests or account limits)
        '''

        self._sort_by['sort'] = metric
        self._sort_by['order'] = order


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
        get top 25 keywords on pages 1 and 2 for provided URL
    ''')

    parser.add_argument('u', metavar='url', type=str, help='url')
    parser.add_argument('-k', metavar='k', type=str, help='semrush apikey')

    args = parser.parse_args()

    q = SERPStatQuery(key=args.k or config.SERP_STAT_TOKEN)

    result = q.request(args.u, limit=10).results

    print(q.request_uri)
    print(json.dumps(result))
