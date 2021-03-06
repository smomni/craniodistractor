import pytest
from config import Config
from cranio.producer import Sensor
from cranio.app import app


def test_start_measurement_transition_prevents_start_if_no_patient_is_selected(
    machine_without_patient,
):
    pytest.helpers.transition_machine_to_s1(machine_without_patient)
    machine = machine_without_patient
    machine.patient_id = ''
    # Try and start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    # Machine stays in state s1
    assert machine.in_state(machine.s1)


def test_start_measurement_transition_prevents_start_if_no_sensor_is_connected(machine):
    pytest.helpers.transition_machine_to_s1(machine)
    # Unregister connected dummy sensor
    machine.main_window.unregister_sensor()
    # Try and start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    # Machine stays in state s1
    assert machine.in_state(machine.s1)


def test_start_measurement_transition_tries_to_automatically_connect_imada_sensor_but_fails_because_configuration_disables_dummy_sensor(
    machine,
):
    pytest.helpers.transition_machine_to_s1(machine)
    # Disconnect sensor
    machine.main_window.unregister_sensor()
    machine.s1.signal_start.emit()
    assert machine.in_state(machine.s1)
    assert machine.main_window.sensor is None


def test_start_measurement_transition_automatically_connects_dummy_sensor_if_imada_not_available_and_configuration_enables_dummy_sensor(
    machine,
):
    pytest.helpers.transition_machine_to_s1(machine)
    Config.ENABLE_DUMMY_SENSOR = True
    try:
        # Disconnect sensor
        machine.main_window.unregister_sensor()
        machine.s1.signal_start.emit()
        assert machine.in_state(machine.s2)
        assert isinstance(machine.main_window.sensor, Sensor)
        machine.s1.signal_stop.emit()
        assert machine.in_state(machine.s6)
    finally:
        Config.ENABLE_DUMMY_SENSOR = False
