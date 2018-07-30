import pytest
import time
import multiprocessing as mp
from functools import partial
from PyQt5.QtCore import QTimer
from daqstore.store import DataStore
from cranio.database import Patient, Document, Session
from cranio.app.window import MainWindow, RegionPlotWindow, NotesWindow

wait_msec = 500


def test_main_window_click_ok_triggers_event_detection_sequence(database_patient_fixture):
    DataStore.queue_cls = mp.Queue
    window = MainWindow()
    # pre-conditions:
    # 1. create, select and lock patient
    window.set_patient(Patient.get_instance().patient_id, lock=True)
    # 2. connect dummy torque sensor
    window.connect_dummy_sensor_action.trigger()
    # 3. measure dummy data (Start -> wait -> Stop)
    window.start_measurement()
    time.sleep(1)
    window.stop_measurement()
    # set timer to close region plot window and click ok
    QTimer.singleShot(wait_msec, window.measurement_widget.region_plot_window.close)
    window.click_ok()
    # kill producer
    window.producer_process.join()


def test_event_detection_sequence_click_ok_triggers_notes_window(database_patient_fixture):
    document = Document(patient_id=Patient.get_instance().patient_id, session_id=Session.get_instance().session_id,
                        distractor_id=1)
    window = RegionPlotWindow(document=document)
    # add regions
    window.set_add_count(2)
    window.add_button_clicked()
    for i in range(window.region_count()):
        window.get_region_edit(i).set_done(True)
    # set timer to close notes window and click ok
    QTimer.singleShot(wait_msec, window.notes_window.close)
    window.ok_button_clicked(user_prompt=False)


def test_event_detection_notes_window_click_ok_closes_the_window(database_patient_fixture):
    document = Document(patient_id=Patient.get_instance().patient_id, session_id=Session.get_instance().session_id,
                        distractor_id=1)
    notes_window = NotesWindow(document)
    notes_window.open()
    assert notes_window.isVisible()
    notes_window.ok_button_clicked(False)
    assert not notes_window.isVisible()

