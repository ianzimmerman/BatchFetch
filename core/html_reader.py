from io import BytesIO
from typing import Any, Callable, Dict, List
from urllib.parse import urljoin, urlsplit

from requests.models import Response
import urllib3 
import requests
from bs4 import BeautifulSoup, Comment

from typing import List
from pydantic import BaseModel, HttpUrl

# import pdfkit

class PropertyTag(BaseModel):
    property: str
    content: str

class MetaTag(BaseModel):
    name: str
    content: str

class MetaReport(BaseModel):
    url: HttpUrl
    domain: str
    user_agent: str
    titles: list
    meta_descriptions: list
    h1s: list
    meta_tags: List[MetaTag]
    og_tags: List[PropertyTag]
    twitter_tags: List[PropertyTag]


def clean(data):
    if isinstance(data, str):
        data = data.strip()
        data = data.replace('\n', '')
        data = data.replace('\r', '')

    return data


class HTMLReader:
    def __init__(self, url: str, custom_header: str = None) -> None:
        self.url = url
        self.domain = None
        
        self.headers = custom_header if custom_header else {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57'
        }

        self.r: Response = None
        try:
            self.soup = self.make_soup()
        except Exception as e:
            pass
        

    def make_soup(self, timeout: int=4) -> Callable[..., BeautifulSoup]:
        try:
            self.r = requests.get(self.url, headers=self.headers, timeout=timeout)
            u = urlsplit(self.r.url)
            self.domain = f'{u.scheme}://{u.netloc}'
        except requests.exceptions.InvalidURL as e:
            raise ValueError(f"{self.url} is not a value URL")
        except urllib3.exceptions.ReadTimeoutError as e:
            raise TimeoutError(f"{self.url} did not respond within {timeout} seconds")
        
        if not self.r.ok:
            raise ConnectionError(f"{self.url} returned a status code of {self.r.status_code} {self.r.reason}")

        if 'html' in self.r.headers['content-type']:
            unicode_str = self.r.content.decode(self.r.apparent_encoding)
            encoded_str = unicode_str.encode("UTF-8", 'ignore')
            return BeautifulSoup(encoded_str, 'html.parser')
        
        raise ValueError(f"{self.url} did not produce valid HTML; Content returned as {self.r.headers['content-type']}")


    @property
    def titles(self) -> List[str]:
        clean_titles = [clean(t.string) for t in self.soup.find('head').find_all('title')]
        return clean_titles

    @property
    def h1s(self) -> List[str]:
        clean_h1s = [clean(t.string) for t in self.soup.find_all('h1')]
        return clean_h1s

    @property
    def meta_descriptions(self) -> List[str]:
        def is_md(tag):
            return tag.name == 'meta' and tag.attrs.get('name') == 'description'

        clean_mds = [clean(t.attrs.get('content'))
               for t in self.soup.find_all(is_md)]

        return clean_mds

    @property
    def meta_tags(self) -> List[MetaTag]:

        def is_meta(tag):
            return all([
                tag.name == 'meta',
                tag.has_attr('name'),
                tag.has_attr('content')
            ])

        meta_tags = [t for t in self.soup.find_all(is_meta)]

        tags: List[Dict[str, str]] = []
        for tag in meta_tags:
            tags.append(
                MetaTag(
                    name=tag.attrs.get('name'),
                    content=tag.attrs.get('content')
                )
            )

        return tags
    
    def property_tags(self, prop_filter=None) -> List[PropertyTag]:
        
        def is_prop(tag):
            return all([
                tag.name == 'meta',
                tag.has_attr('property'),
                tag.has_attr('content')
            ])

        prop_tags = self.soup.find_all(is_prop)

        if prop_filter:
            ''' og: twitter: and others'''
            prop_tags = [t for t in prop_tags if t.attrs.get('property').startswith(prop_filter)]

        tags = []
        for tag in prop_tags:
            tags.append(
                PropertyTag(
                    property=tag.attrs.get('property'),
                    content=tag.attrs.get('content')
                )
            )

        return tags
    
    @property
    def meta_report(self) -> MetaReport:
        report = {
            'url': self.r.url,
            'domain': self.domain,
            'user_agent': self.headers['User-Agent'],
            'titles': self.titles,
            'meta_descriptions': self.meta_descriptions,
            'h1s': self.h1s,
            'meta_tags': self.meta_tags,
            'og_tags': self.property_tags('og:'),
            'twitter_tags': self.property_tags('twitter:'),
        }

        return MetaReport(**report)
    
    @staticmethod
    def csv_headers() -> List[str]:
        return ['url', 'domain', 'title', 'meta_description', 'h1']

    @property
    def csv_report(self) -> Dict[str, str]:
        report = {
            'url': self.r.url,
            'domain': self.domain,
            'title': self.titles[0] if self.titles else '',
            'meta_description': self.meta_descriptions[0] if self.meta_descriptions else '',
            'h1': self.h1s[0] if self.h1s else '',
        }

        return report

    def schema_from_attrs(self, test_name: str):
        ''' 
            extract schemas from itemscopes
            
            Consider:
            <div itemscope itemtype="https://schema.org/Drug">
                <span itemprop="name">Ibuprofen</span> is a non-steroidal
                anti-inflammatory medication, indicated for temporary relief
                of minor aches and pains due to
                <span itemprop="indication" itemscope itemtype="https://schema.org/TreatmentIndication">
                    <span itemprop="name">headache</span>
                </span>,
                <span itemprop="indication" itemscope itemtype="https://schema.org/TreatmentIndication">
                    <span itemprop="name">toothache</span>
                </span>, ...
            </div>

            Should produce:

            {
                '@context': 'https://schema.org',
                '@type': 'Drug',
                'name': 'Ibuprofen',
                'indication': [
                    {
                        '@context': 'https://schema.org',
                        '@type': 'TreatmentIndication',
                        'name': 'headache'
                    },
                    {
                        '@context': 'https://schema.org',
                        '@type': 'TreatmentIndication',
                        'name': 'toothache'
                    }
                ]
            }
        
        '''

        with open(f"/Users/ian/git/BatchHTML/services/app/core/htmlreader/tests/{test_name}.html") as fp:
            print(fp)
            self.soup = BeautifulSoup(fp, 'html.parser')

        def is_parentscope(tag):
            return all([
                tag.has_attr('itemscope'),
                tag.has_attr('itemtype'),
                not tag.has_attr('itemprop')
            ])

        def is_itemscope(tag):
            return all([
                tag.has_attr('itemscope'),
                tag.has_attr('itemtype')
            ])

        def is_itemprop(tag):
            return tag.has_attr('itemprop')
        
        def _prop_value(tag: Any):
            if tag.attrs.get('itemtype'):
                return process_scope(tag)

            if href_value := tag.attrs.get('href'):
                return href_value
            elif src_value := tag.attrs.get('src'):
                return src_value
            elif content_value := tag.attrs.get('content'):
                return content_value
            else:
                return tag.get_text()
        
        def process_scope(scope: Any):
            if itemtype := scope.attrs.get('itemtype'):
                at_type = itemtype.split('/')[-1]
                new_scope = {
                    '@context': 'https://schema.org',
                    '@type': at_type
                }

                prop_tags = scope.find_all(is_itemprop) # , recursive=False)
                for t in prop_tags:
                    parent_scope = t.find_parent(attrs={'itemtype': True})
                    if parent_scope.attrs.get('itemtype') != itemtype:
                        continue

                    prop_name = t.attrs.get('itemprop')
                    prop_value = _prop_value(t)

                    if existing_prop := new_scope.get(prop_name):
                        if isinstance(existing_prop, list):
                            new_scope[prop_name].append(prop_value)
                        else:
                            new_scope[prop_name] = [
                                existing_prop,
                                prop_value
                            ]
                    else:
                        new_scope[prop_name] = prop_value

                return new_scope
            else:
                return None

        itemscopes = [ps.extract() for ps in self.soup.find_all(is_parentscope)]
        scopes = []
        for scope in itemscopes:
            if new_scope := process_scope(scope):
                scopes.append(new_scope)
        
        return scopes


    def embeddable_html(self, convert_tags=True):
        ''' convert html to absolute URLs and add base tag to open links in new tab '''
        if not self.html:
            return None

        base = self.soup.new_tag('base', href=self.domain, target='_blank_xap')
        self.soup.head.insert(0, base)

        def make_absolute(tag, attr):
            for t in self.soup.select('{0}[{1}]'.format(tag, attr)):
                if not (t[attr].startswith('http') or t[attr].startswith('//')):
                    t[attr] = urljoin(self.r.url, t[attr])
        
        for i in self.soup.select('iframe'):
            i.extract()

        if convert_tags:
            tags = [
                ('source', 'srcset'), ('img', 'src'), ('img', 'srcset'),
                ('script', 'src'), ('link', 'href'), ('a', 'href')
            ]

            for tag, attr in tags:
                make_absolute(tag, attr)

        comments = self.soup.findAll(
            text=lambda text: isinstance(text, Comment))
        for c in comments:
            c.extract()

        scripts = self.soup.findAll(name='script')
        for s in scripts:
            if 'window.location.reload()' in str(s):
                s.extract()
            
            if 'boomerang' in str(s):
                s.extract()
            
            if 'trustarc' in s.get('src', ''):
                s.extract()
        
        links = self.soup.findAll(name='link')
        for l in links:
            if 'boomerang' in str(l):
                l.extract()

        result = str(self.soup).replace(
            'top.location', 'var a'
        ).replace(
            'none !important', 'inline'
        ).replace(
            'window.location.reload();', ''
        )

        # with open('temp.html', 'w') as f:
        #     f.write(result)

        return result

    def html_to_bytes(self):
        f = BytesIO()
        f.write(self.embeddable_html(True).encode("UTF-8"))
        f.seek(0)

        return f
