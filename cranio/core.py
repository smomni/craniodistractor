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
import uuid
import json
import io
import pickle
import random
import attr
import pandas as pd
from collections import namedtuple
from typing import Tuple
from contextlib import contextmanager
from datetime import datetime

def generate_unique_id():
    ''' Return unique id based on host ID, sequence number and current time '''
    return str(uuid.uuid1())

def timestamp():
    ''' Return current date and time (UTC+0) '''
    return datetime.utcnow()

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
    
    def as_tuple(self):
        ''' Converts the Packet to a tuple (index, data_dict) '''
        return (self.index, self.data)
    
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
    
@attr.s
class SessionMeta:
    patient_id = attr.ib()
    session_id = attr.ib(default=attr.Factory(generate_unique_id))
    datetime = attr.ib(default=None)
    
Attachment = namedtuple('Attachment', ['content', 'filename', 'content_type'])

class Session:
    
    def __init__(self, patient_id, _id=None, datetime=None, data=None, log=None):
        if _id is None:
            _id = generate_unique_id()
        self._id = _id
        self.patient_id = patient_id
        self.datetime = datetime
        self.data = data
        self.log = log
    
    def as_document(self) -> dict:
        ''' Return the session as a document that can be uploaded to a CouchDB database '''
        return {'_id': self._id, 'patient_id': self.patient_id, 'datetime': self.datetime}
    
    @contextmanager
    def data_io(self) -> io.StringIO:
        ''' Return the session data as a file-like object '''
        # data to file-like object
        dio = io.StringIO()
        self.data.to_csv(dio, sep=';')
        dio.seek(0)
        yield dio
        dio.close()
    
    @contextmanager
    def log_io(self) -> io.StringIO:
        ''' Return the session log as a file-like object '''
        # log to file-like object
        lio = io.StringIO()
        lio.write(self.log)
        lio.seek(0)
        yield lio
        lio.close()
    
    def attachments(self) -> Tuple[Attachment]:
        ''' Return the session attachments (i.e., data and log) as file-like objects '''
        with self.data_io() as f:
            data = Attachment(content=f.read(), filename=self._id + '.csv', content_type='text/csv')
        with self.log_io() as f:
            log = Attachment(content=f.read(), filename=self._id + '.log', content_type='text/plain')
        return (data, log)
    
    def save(self, path):
        ''' Save the session on disk '''
        with open(path, 'w') as f:
            json.dump(self.as_document(), f)
    
    @classmethod
    def load(cls, path):
        ''' Load a session from disk '''
        with open(path, 'r') as f:
            return cls(**json.load(f))
