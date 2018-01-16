'''
Implements a serializable Packet object for data transfer over separate processes

Copyright (C) 2017  Simo Tumelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import pickle
import random
import attr
import pandas as pd

def event_identifier(event, num):
    return '{}{:03d}'.format(event, num)

def x_smaller_than_y(instance, attribute, value):
    if value >= instance.y:
        raise ValueError("'x' has to be smaller than 'y'!")

@attr.s
class Event:
    DISTRACTION = 'D'
    
    type = attr.ib(validator=attr.validators.instance_of(str))
    num = attr.ib(validator=attr.validators.instance_of(int))
    
    @num.validator
    def num_positive_and_less_than_1000(self, attribute, value):
        if not 0 <= value < 1000:
            raise ValueError('Event number must be less than 1000')
        
    def __str__(self):
        return event_identifier(self.type, self.num)
    
class Packet:
    ''' Container for moving data between processes '''
    
    def __init__(self, index, data):
        '''
        Args:
            - index: index values (e.g., time stamps)
            - data: data as a dictionary
        '''
        self.index = index
        self.data = data
        
    def __eq__(self, other):
        return self.index == other.index and self.data == other.data
        
    def encode(self):
        ''' Encodes the Packet as bytes '''
        return pickle.dumps(self)
    
    @classmethod
    def decode(cls, data):
        ''' Decodes bytes back to a Packet object '''
        return pickle.loads(data)
    
    def as_dataframe(self) -> pd.DataFrame:
        ''' Converts the Packet to a pd.DataFrame '''
        return pd.DataFrame(self.data, index=self.index)
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        ''' Initializes a Packet from a pd.DataFrame '''
        return cls(index=list(df.index.values), data=df.to_dict(orient='list'))
    
    @classmethod
    def random(cls):
        ''' Creates a Packet with random data '''
        return Packet(index=[random.random()], data={'value': [random.random()]})
    
    @classmethod
    def concat(cls, packets):
        ''' Inefficient concat utilizing pd.concat '''
        return cls.from_dataframe(pd.concat([p.as_dataframe() for p in packets]))
