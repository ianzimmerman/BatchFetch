import csv
import json
from io import BytesIO
from typing import List, Optional
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import urlopen

import core.apis.config as config
import requests
from core.apis import AbstractQuery
from pydantic import BaseModel, HttpUrl


class QueryResult(BaseModel):
    ph: str
    po: int
    pd: Optional[str]
    tr: float
    nq: int
    et: int
    ur: HttpUrl
    td: Optional[str]


class SEMRushQuery(AbstractQuery):
    def __init__(self, key=None):
        self.url = None
        self.domain = None
        self.query_type = 'url_organic'
        self.key = key or config.SEMRUSH_TOKEN
        self.database = 'us'
        self.filter_list = []

        # if self.domain:
        #     self.add_filter('+', 'Ur', 'Co', self.domain)

        self.set_columns()

        self._headers = [
            ('ph','Keyword'),
            ('po','Position'),
            ('pd','Position Difference'),
            ('tr','Traffic (%)'),
            ('nq','Search Volume'),
            ('et','Estimated Monthly Traffic'),
            ('ur','Url'),
            ('td','Trends')
        ]
    
    @staticmethod
    def headers():
        return [
            'ph',
            'po',
            'pd',
            'tr',
            'nq',
            'et',
            'ur',
            'td',
        ]

    def add_filter(self, sign, field, operation, value):
        """
        Add filter for returned values. Max 25 filters:
        https://www.semrush.com/api-analytics/#filters
        """
        args = [sign, field, operation, str(value)]

        if len(self.filter_list) < 25:
            self.filter_list.append('|'.join(args))
        else:
            print('Filter not added: Too Many Filters')

        return self

    def filters(self):
        if len(self.filter_list) > 0:
            return '|'.join(self.filter_list)
        else:
            return None

    def set_columns(self, cols=['Ph', 'Po', 'Pd', 'Tr', 'Nq', 'Ur', 'Vu']):
        """
        Set return columns as list e.g. ['col1','col2']:
        https://www.semrush.com/api-analytics/#columns
        """
        self.columns = cols
        self.col_string = ','.join(cols)

        return self

    def args(self):
        params = {
            'type': self.query_type,
            'key': self.key,
            'display_limit': self.row_limit,
            'export_columns': self.col_string,
            'display_filter': self.filters(),
            'display_sort': self.sort_by,
            'database': self.database,
            'export_escape': 1
        }

        if self.url:
            params['url'] = self.url

        if self.domain:
            params['domain'] = self.domain

        if self.filters() is None:
            params.pop('display_filter', None)

        return params

    def request(self, query, limit=25, method='url_organic', se='us'):
        """
        Returns a double quote (") escaped CSV with a ; separator
        as a ByteIO stream
        row_limit required (Max 10,000)
        """
        self.url = query
        self.query_type = method
        self.database = se
        self.row_limit = min(limit, 10000)
        self.sort_by = 'tr_desc'

        args = urlencode(self.args(), safe=',', quote_via=quote)
        self.request_uri = f"{config.SEMRUSH_ENDPOINT}/?{args}"

        self.response = requests.get(self.request_uri)
        return self
    
    def request_volume(self, phrase, se='us'):
        args = {
            'type': 'phrase_this',
            'phrase': phrase,
            'key': self.key,
            'database': self.database,
            'export_escape': 1,
            'export_columns': ','.join(['Ph', 'Nq', 'Td'])
        }
        args = urlencode(args, safe=',', quote_via=quote)
        self.request_uri = f"{config.SEMRUSH_ENDPOINT}/?{args}"
        self.response = requests.get(self.request_uri)
        
        return self

    @property
    def results(self) -> List[QueryResult]:
        if self.response.text.startswith("ERROR"):
            return []
        else:
            # print(self.response.text)
            rows = self.response.text.split("\r\n")
            headers = [h for h in rows.pop(0).split(";")]
            keywords = []

            for r in rows:
                row = r.split(";")
                if len(row) is not len(headers):
                    continue

                data = {}
                data['ur'] = self.url

                for i, h in enumerate(headers):
                    data[self.unmap(h)] = unquote(
                        row[i],
                        errors="replace"
                    )[1:-1]

                if all([data.get('po'), data.get('nq')]):
                    ctrs = [.3844, .1907, .1134, .077, .0546,
                            .0409, .0315, .0249, .0199, .0171,
                            .0177, .0192, .0192, .0188, .0189,
                            .0173, .0163, .0152, .0142, .0131]

                    try:
                        data['et'] = round(
                            ctrs[int(data.get('po'))-1] * int(data.get('nq'))
                        )
                    except IndexError:
                        data['et'] = 0

                else:
                    data['et'] = 0

                keywords.append(data)

            return [QueryResult(**k) for k in keywords]

    def keyword_results(self):
        if self.response.text.startswith("ERROR"):
            return None
        else:
            rows = self.response.text.split("\r\n")
            headers = [h for h in rows.pop(0).split(";")]
            values = [v for v in rows.pop(0).split(";")]

            return dict(zip(headers, values))

    def unmap(self, header):
        map = { h[1]: h[0] for h in self._headers}

        try:
            return map[header]
        except IndexError:
            return header
    
    def remap(self, header):
        map = { h[0]: h[1] for h in self._headers}

        try:
            return map[header]
        except IndexError:
            return header
