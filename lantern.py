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
        
        self._group_name = None
    
    @property
    def group_name(self):
        # TODO: work around until I know how to get groups directly
        if self._group_name is None:
            today = self.today()
            self._group_name = today['group_name']
        return self._group_name
        
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

    def _get(self, group, view, start, json=True):
        url = os.path.join(self.base_url, f'energy/group/{group}/{view}/{start}')
        
        response = self.session.get(url)
        
        if json is True:
            return response.json()
        else:
            return response

    def today(self, group=1):
        return self._get(group, 'DAY', self.start_of_day())
        
    def month(self, group=1):
        return self._get(group, 'MONTH', self.start_of_month())

    def year(self, group=1):
        return self._get(group, 'YEAR', self.start_of_year())


if __name__ == '__main__':
    lantern = Lantern(os.environ['LANTERN_USER'], os.environ['LANTERN_PASSWORD'])
