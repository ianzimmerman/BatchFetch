from abc import ABC, abstractmethod, abstractproperty

class AbstractQuery(ABC):
    @abstractmethod
    def __init__(self, api_key:str):
        ''' api key for service '''
        super().__init__(api_key)

    @abstractproperty
    def headers(self):
        ''' str list of header values '''
        pass
    
    @abstractmethod
    def request(self, query:str, limit:int, method:str, se:str):
        ''' 
            http request for passed query
            for QUERY get METHOD on SE (search engine country code)
        '''
        pass

    @abstractproperty
    def results(self):
        ''' convert result to list of dictionaries mapped to headers '''
        pass