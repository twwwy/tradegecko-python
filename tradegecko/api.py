import logging
import requests
import json
import time
import math

logger = logging.getLogger(__name__)


class TGRequestFailure(Exception):
    pass


class ApiEndpoint(object):

    def __init__(self, base_data, access_token):
        self.base_data = base_data
        self.access_token = access_token
        self.header = {
            'Authorization': 'Bearer ' + self.access_token,
            'content-type': 'application/json'
        }
        self.rsp = None
        self.json = None
        self.base_uri = 'https://api.tradegecko.com/'
        self.uri = ''
        self.required_fields = []
        self._data_name = ''

    def _validate_post_data(self, data):
        for k in self.required_fields:
            if k not in data.keys():
                return False
        return True


    def _send_request(self, method, uri, data=None, params=None):
        fails = 0
        while fails < 2:
            self.rsp = requests.request(method, uri, data=data, headers=self.header, params=params)
            logger.info('TRADEGECKO API REQUEST: %s %s \nDATA="%s" \nRESPONSE="%s" \nSTATUS_CODE: %s' % (method, uri, data, self.rsp.content, self.rsp.status_code))
            if self.rsp.status_code == 429:
                retry_after = int(self.rsp.headers.get('retry-after', 10))
                time.sleep(retry_after)
                fails += 1
            else:
                break
        return self.rsp.status_code

    def _build_data(self, data):
        return json.dumps({self._data_name: data})

    # all records
    def all(self, page=1):
        params = {'page': page}
        if self._send_request('GET', self.uri, params=params) == 200:
            return self.rsp.json()
        else:
            return False

    # retrieve a specific record
    def get(self, pk):
        uri = self.uri + str(pk)
        if self._send_request('GET', uri) == 200:
            return self.rsp.json()
        else:
            return False

    # records filtered by field value
    def filter(self, **kwargs):
        if self._send_request('GET', self.uri, params=kwargs) == 200:
            return self.rsp.json()
        else:
            return False

    # delete a specific record
    def delete(self, pk):
        uri = self.uri + str(pk)
        if self._send_request('DELETE', uri) == 204:
            return self.rsp
        else:
            return False

    # create a new record
    def create(self, data):
        data = self._build_data(data)

        if self._send_request('POST', self.uri, data=data) == 201:
            return self.rsp.json()[self._data_name]['id']
        else:
            raise TGRequestFailure("Creation Failed")

    # update a specific record
    def update(self, pk, data):
        uri = self.uri + str(pk)
        data = self._build_data(data)

        if self._send_request('PUT', uri, data=data) == 204:
            return True
        else:
            raise TGRequestFailure("Update Failed")

    def page_count(self, limit=100):
        tg_items = self.filter(page='1', limit='1')
        return int(math.ceil(tg_items['meta']['total'] / float(limit)))

