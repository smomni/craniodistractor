import os
import pytest
import pandas as pd
import numpy as np
import couchdb
from contextlib import suppress
from cranio.core import Session, Attachment

COUCHDB_URL = 'http://127.0.0.1:5984/'
DATABASE_NAME = 'craniodistractor'
        
@pytest.fixture
def session():
    # assing random data
    s = Session(patient_id='test_patient', 
                data=pd.DataFrame(data=np.random.rand(100, 3), columns=list('ABC')),
                log='abc')
    yield s
    
@pytest.fixture
def path():
    p = 'session.json'
    yield p
    with suppress(FileNotFoundError):
        os.remove(p)
        
@pytest.fixture
def couchserver():
    server = couchdb.Server(COUCHDB_URL)
    yield server
    
@pytest.fixture
def db(couchserver):
    try:
        db = couchserver[DATABASE_NAME]
    except couchdb.http.ResourceNotFound:
        db = couchserver.create(DATABASE_NAME)
    yield db
        
def test_Session_init_with_keyword_arguments():
    session = Session(patient_id='123')
    assert session._id is not None
    assert session.patient_id is '123'
    # no keyword arguments
    with pytest.raises(TypeError):
        Session()

def test_Session_save_and_load(session, path):
    session.save(path)
    s2 = Session.load(path)
    assert session.as_document() == s2.as_document()
    
def test_Session_data_and_log_io(session):
    # verify data integrity after reading from io object
    with session.data_io() as dio:
        df = pd.read_csv(dio, sep=';', index_col=0)
    pd.testing.assert_frame_equal(df, session.data)
    # verify log integrity after reading from io object
    with session.log_io() as lio:
        assert lio.read() == session.log

@pytest.mark.couchdb
def test_Session_to_couchdb(db, session):
    doc = session.as_document()
    doc_id, rev_id = db.save(doc)
    # put attachments
    for attachment in session.attachments():
        db.put_attachment(db[doc_id], **attachment._asdict())
    # read attachments and verify contents
    for attachment in session.attachments():
        bytesio = db.get_attachment(doc_id, attachment.filename)
        assert bytesio.read().decode() == attachment.content
    # delete document
    db.delete(db[doc_id])