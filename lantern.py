import base64
from datetime import datetime
import os
import requests
import struct


# joules / 3600000
JOULES_TO_KWH = 3600000


def flatten(sub_groups):
    for sub_group in sub_groups:
        if 'sub_groups' in sub_group:
            yield from flatten(sub_group['sub_groups'])
        else:
            yield sub_group


def decode_block_to_kwh(group):
    b64 = group['blocks']['$binary']['base64']
    binary = base64.b64decode(b64)
    # struct unpack aslways returns a tuple even if one element
    return [f[0] / 3600000.0 for f in struct.iter_unpack('>f', binary)]


class Lantern:
    def __init__(self, user, password, dt=None):
        # https://lanternsoftware.com/currentmonitor/energy/group/<group_id>/<view>/<start>
        self.base_url = 'https://lanternsoftware.com/currentmonitor'
        self.auth_url = os.path.join(self.base_url, 'auth')
        
        auth_code = requests.get(self.auth_url, auth=(user, password)).json()['auth_code']
        self.session = requests.Session()
        # self.session.auth = (user, password)
        
        # auth_code = self.session.get(self.auth_url).json()['auth_code']
        self.session.headers.update({'auth_code': auth_code})
        
        if dt is None:
            self.dt = datetime.now()
        else: 
            self.dt = dt
        
        self._config = None
    
    @property
    def config(self):
        if self._config is None:
            endpoint = 'config'
            self._config = self._get(endpoint)
        return self._config 

    @property
    def group_name(self):
        # TODO: get the name from the selected group later
        return self.config['breaker_groups'][0]['name']
    
    @property
    def group_ids(self):
        config = self.config
        breaker_groups = config['breaker_groups']
        return [breaker_group['_id'] for breaker_group in breaker_groups]
        
    def start_of_day(self):
        """Start of the day from datetime object"""
        midnight = self.dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(midnight.timestamp()) * 1000

    def start_of_month(self):
        """Start of the month from datetime object"""
        midnight = self.dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return int(midnight.timestamp()) * 1000

    def start_of_year(self):
        """Start of the year from datetime object"""
        midnight = self.dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return int(midnight.timestamp()) * 1000

    def _get(self, endpoint, json=True):
        url = os.path.join(self.base_url, endpoint)
        
        response = self.session.get(url)
        
        if json is True:
            return response.json()
        else:
            return response

    def today(self):
        group = self.group_ids[0]
        endpoint = f'energy/group/{group}/DAY/{self.start_of_day()}'
        return self._get(endpoint)
        
    def month(self):
        # TODO: grab the first group for now
        group = self.group_ids[0]
        endpoint = f'energy/group/{group}/MONTH/{self.start_of_month()}'
        return self._get(endpoint)

    def year(self):
        group = self.group_ids[0]
        endpoint = f'energy/group/{group}/YEAR/{self.start_of_year()}'
        return self._get(endpoint)


if __name__ == '__main__':
    lantern = Lantern(os.environ['LANTERN_USER'], os.environ['LANTERN_PASSWORD'])
