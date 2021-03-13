import base64
from dataclasses import dataclass, field
from datetime import datetime
import os
import requests
import struct
from typing import List


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


@dataclass
class Breaker:
    panel: int
    space: int
    meter: int
    hub: int
    port: int
    name: str
    size_amps: int
    calibration_factor: float
    low_pass_filter: float
    polarity: str
    double_power: bool
    type: str
    description: str = ''


class Panel:
    def __init__(self, account_id, name, index, spaces, meter, breakers=None):
        self.account_id = account_id
        self.name = name
        self.index = index
        self.spaces = spaces
        self.meter = meter

        if breakers is None:
            self.breakers = []
        
        self._space_map = None

    @property
    def space_map(self):
        if self._space_map is None:
            spaces = {index: None for index in range(1, self.spaces)}

            for breaker in self.breakers:
                spaces[breaker.space] = breaker
            
            self._space_map = spaces
            
        return self._space_map
    
    def __repr__(self):
        args = ', '.join(f'{k}={v}' for k, v in vars(self).items())
        return f'Panel({args})'


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
        return self.config['breaker_groups'][0]['name']
    
    @property
    def group_id(self):
        return self.config['breaker_groups'][0]['_id']
        
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
        endpoint = f'energy/group/{self.group_id}/DAY/{self.start_of_day()}'
        return self._get(endpoint)
        
    def month(self):
        # TODO: grab the first group for now
        endpoint = f'energy/group/{self.group_id}/MONTH/{self.start_of_month()}'
        return self._get(endpoint)

    def year(self):
        endpoint = f'energy/group/{self.group_id}/YEAR/{self.start_of_year()}'
        return self._get(endpoint)


if __name__ == '__main__':
    l = Lantern(os.environ['LANTERN_USER'], os.environ['LANTERN_PASSWORD'])
