"""
Finite-state machine.
"""
from PyQt5.QtCore import QStateMachine, QState, pyqtSignal
from cranio.app.window import MainWindow
from cranio.model import Session, Database
from cranio.state import (
    InitialState,
    MeasurementState,
    EventDetectionState,
    AreYouSureState,
    NoteState,
    ChangeSessionState,
    ShowPatientsState,
    AddPatientState,
    FinalState,
)
from cranio.transition import (
    StartMeasurementTransition,
    ChangeActiveSessionTransition,
    UpdateDocumentTransition,
    AddPatientTransition,
    SetPatientTransition,
)


class StateMachine(QStateMachine):
    # Hidden transition trigger signals for testing purposes
    _s1_to_s3_signal = pyqtSignal()
    _s1_to_s6_signal = pyqtSignal()

    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        self.main_window = MainWindow(database)
        self.document = None
        self.annotated_events = None
        self._session = None
        self._initialize_states()
        self._initialize_transitions()

    def _initialize_states(self):
        self.s0 = ShowPatientsState(name='s0')
        self.s0_1 = AddPatientState(name='s0_1')
        self.s1 = InitialState(name='s1')
        self.s2 = MeasurementState(name='s2')
        self.s3 = EventDetectionState(name='s3')
        self.s4 = AreYouSureState(
            'Are you sure you want to continue without annotating '
            'any events for the recorded data?',
            name='s4',
        )
        self.s6 = NoteState(name='s6')
        self.s7 = AreYouSureState('Are you sure you want to continue?', name='s7')
        self.s9 = ChangeSessionState(name='s9')
        self.s10 = AreYouSureState(
            'You have selected session {session_info}. '
            'Are you sure you want to continue?',
            name='s10',
        )
        self.s11 = AreYouSureState(
            'Are you sure you want to exit the application?', name='s11'
        )
        self.s_final = FinalState(name='s_final')
        for s in (
            self.s_final,
            self.s0,
            self.s0_1,
            self.s1,
            self.s2,
            self.s3,
            self.s4,
            self.s6,
            self.s7,
            self.s9,
            self.s10,
            self.s11,
        ):
            self.addState(s)
        self.setInitialState(self.s0)
        # Additional initializations
        self.s0.init_ui()
        self.s9.init_ui()

    def _initialize_transitions(self):
        self.set_patient_transition_on_close = SetPatientTransition(
            self.s0.signal_close
        )
        self.set_patient_transition_on_close.setTargetState(self.s1)
        self.set_patient_transition_on_ok = SetPatientTransition(self.s0.signal_ok)
        self.set_patient_transition_on_ok.setTargetState(self.s1)
        self.add_patient_transition = AddPatientTransition(self.s0_1.signal_ok)
        self.add_patient_transition.setTargetState(self.s0)
        self.start_measurement_transition = StartMeasurementTransition(
            self.main_window.signal_start
        )
        self.start_measurement_transition.setTargetState(self.s2)
        self.change_active_session_transition = ChangeActiveSessionTransition(
            self.s10.signal_yes
        )
        self.change_active_session_transition.setTargetState(self.s1)
        self.update_document_transition = UpdateDocumentTransition(self.s7.signal_yes)
        self.update_document_transition.setTargetState(self.s1)
        self.transition_map = {
            self.s0: {
                self.s0_1: self.s0.signal_add_patient,
                self.s1: [
                    self.set_patient_transition_on_close,
                    self.set_patient_transition_on_ok,
                ],
            },
            self.s0_1: {
                self.s0: [self.s0_1.signal_cancel, self.add_patient_transition]
            },
            self.s1: {
                self.s2: self.start_measurement_transition,
                self.s6: self._s1_to_s6_signal,
                self.s9: self.s1.signal_change_session,
                self.s11: self.main_window.signal_close,
            },
            self.s2: {self.s6: self.main_window.signal_stop},
            self.s3: {self.s4: self.s3.signal_close},
            self.s4: {self.s3: self.s4.signal_no},
            self.s6: {self.s7: self.s6.signal_ok},
            self.s7: {
                self.s6: self.s7.signal_no,
                self.s1: self.update_document_transition,
            },
            self.s9: {self.s10: self.s9.signal_select, self.s1: self.s9.signal_cancel},
            self.s10: {
                self.s9: self.s10.signal_no,
                self.s1: self.change_active_session_transition,
            },
            self.s11: {self.s1: self.s11.signal_no, self.s_final: self.s11.signal_yes},
        }
        # Add transitions to state machine
        for source, targets in self.transition_map.items():
            for target, signal_arr in targets.items():
                if not isinstance(signal_arr, list):
                    signal_arr = [signal_arr]
                for signal in signal_arr:
                    if hasattr(signal, 'custom_signal'):
                        source.addTransition(signal)
                    else:
                        source.addTransition(signal, target)

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, value: Session):
        self._session = value

    @property
    def session_id(self) -> str:
        return self.session.session_id

    @property
    def patient_id(self) -> str:
        return self.main_window.patient_id

    @patient_id.setter
    def patient_id(self, patient_id: str):
        self.main_window.patient_id = patient_id

    @property
    def distractor(self):
        return self.main_window.measurement_widget.distractor

    @property
    def operator(self):
        return self.main_window.meta_widget.operator

    @property
    def producer_process(self):
        return self.main_window.producer_process

    @property
    def sensor(self):
        return self.main_window.sensor

    @property
    def sensor_serial_number(self):
        return self.main_window.sensor.sensor_info.sensor_serial_number

    @property
    def session_id(self):
        return self.session.session_id

    @property
    def distractor_type(self):
        from config import Config

        return Config.DEFAULT_DISTRACTOR

    def in_state(self, state: QState) -> bool:
        """
        Determine if the state machine in a specified state.

        :param state:
        :return:
        """
        return state in self.configuration()

    def current_state(self) -> QState:
        """
        Return the current state the machine is in.

        :raises ValueError: If current state is not defined
        :return:
        """
        active_states = self.configuration()
        if len(active_states) != 1:
            raise ValueError(
                f'Current state not defined if {len(active_states)} states are active simultaneously'
            )
        return list(active_states)[0]

    def connect_sensor(self):
        self.main_window.connect_imada_sensor()

    def connect_dummy_sensor(self):
        self.main_window.connect_dummy_sensor()
