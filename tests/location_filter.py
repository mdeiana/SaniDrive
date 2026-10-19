import time
import unittest
from typing import Any
from pathlib import Path
from builtins import list
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from sanidrive import sanidrive
from sanidrive.location import Location
from unittest.mock import MagicMock, patch
from sanidrive.appointment import Appointment

PLACES = ['Via IV Novembre snc - ALES (OR)',
          'CORSO IV NOVEMBRE - SORGONO (NU)',
          'VIA ANTONIO GIAGU - SASSARI (SS)',
          'Via IV Novembre snc - ALES (OR)', '- BONO (SS)', '- OZIERI (SS)',
          '- OLBIA (OT)', 'Viale San Pietro n°43/b - SASSARI (SS)',
          'VIA CATTANEO - IGLESIAS (CI)',
          'Via Berlinguer - SANTA TERESA GALLURA (OT)',
          "Loc. Sant' Efisio - SINISCOLA (NU)",
          "Via Turati - QUARTU SANT'ELENA (CA)",
          "Via Turati - QUARTU SANT'ELENA (CA)",
          'P.zza Europa n°1 - DOLIANOVA (CA)', 'Viale Arsia - CARBONIA (CI)',
          'Strada Statale 554 - bivio Sestu - MONSERRATO (CA)',
          '- IGLESIAS (CI)']

DATES = ['Martedì 20 Ottobre 2026', 'Venerdì 23 Ottobre 2026',
         'Martedì 24 Novembre 2026', 'Mercoledì 9 Dicembre 2026',
         'Lunedì 14 Dicembre 2026', 'Mercoledì 16 Dicembre 2026',
         'Giovedì 17 Dicembre 2026', 'Venerdì 22 Gennaio 2027',
         'Martedì 2 Marzo 2027', 'Mercoledì 3 Marzo 2027',
         'Mercoledì 16 Giugno 2027', 'Lunedì 28 Giugno 2027',
         'Martedì 29 Giugno 2027', 'Mercoledì 30 Giugno 2027',
         'Venerdì 9 Luglio 2027', 'Lunedì 13 Settembre 2027',
         'Lunedì 27 Settembre 2027']

TIMES = ['09:00', '08:30', '12:00', '08:00', '09:00', '09:00', '09:30',
         '09:20', '09:30', '08:30', '08:30', '07:45', '08:10', '15:00',
         '11:00', '09:00', '08:00']

NOTES = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']


class SpyList(list):
    appended_appointments = []
    def append(self, object: Any) -> None:
        if isinstance(object, Appointment):
            print('\t\t\tSpyList.append called')
            self.appended_appointments.append(object)
        return super().append(object)

original_Appointment = Appointment
class SpyAppointment(original_Appointment):
    captured_appointments = []
    def __init__(self, place: str, date: str, time: str, notes: str):
        # don't include "earliest_appointment"
        if any((place, date, time, notes)):
            self.captured_appointments.append(
                Appointment(place, date, time, notes))
        super().__init__(place, date, time, notes)

    def is_sooner_than(self, other: Appointment) -> bool:
        print('is_sooner_than called')
        return breaker.watch(super().is_sooner_than, other)
        #return super().is_sooner_than(other)

class IntentionalLoopBreakException(Exception):
    pass

class LoopBreaker():
    def __init__(self, max_loops = 1) -> None:
        self.max_loops = max_loops
        self.times_looped = 0

    def watch(self, handle, *args) -> Any:
        print('LoopBreaker.watch called')
        if self.times_looped >= self.max_loops:
            raise IntentionalLoopBreakException
        else:
            self.times_looped += 1
            return handle(*args)

class MockChromeDriver(webdriver.Chrome):
    def __init__(self, options: Options | None = None, service: Service
                 | None = None, keep_alive: bool = True) -> None:
        super().__init__(options, service, keep_alive)
        self.get_dl_page()
        time.sleep(1)

    def get_dl_page(self):
        file_path = Path(__file__).parent / 'data' / 'appointment_list_page.html'
        self.get('file:///' + file_path.__str__())

original_is_sooner_than = Appointment.is_sooner_than
breaker = LoopBreaker(0)

class TestLocationFilterV2(unittest.TestCase):
    def setUp(self) -> None:
        driver = MockChromeDriver()

        self.locations = [
            Location('Tortolì', 20.0, []),
            Location('Serramanna', 25.0, []),
            Location('Ales', 0.0, []),
            Location("Quartu Sant'Elena", 0.0, []),
            Location('Iglesias', 0.0, [])
        ]

        patchers = [
            patch('sanidrive.sanidrive.init_driver',
                  return_value=driver),    # 0
            patch('sanidrive.sanidrive.list'),   # 1
            patch('sanidrive.sanidrive.print'),
            patch('sanidrive.sanidrive.cls'),
            patch('sanidrive.sanidrive.choose_prescription'),    # 4
            patch('sanidrive.sanidrive.read_prescriptions'),
            
            patch('sanidrive.sanidrive.interactive_latest_appointment',
                  return_value=SpyAppointment.latest([''])),
            patch('sanidrive.sanidrive.interactive_location_v2',
                  return_value=self.locations),   # 8
            patch('sanidrive.sanidrive.get_appointments_page'),
            patch('sanidrive.sanidrive.expand_list'),
            patch('sanidrive.sanidrive.Appointment', new=SpyAppointment),
            patch('sanidrive.sanidrive.title'),
            patch('sanidrive.sanidrive.divider')
        ]

        self.mocks = []
        for p in patchers:
            self.mocks.append(p.start())

        self.addCleanup(patch.stopall)
        return super().setUp()


    def helper_fn(self) -> None:
        pass


    def test_perfect_matches_no_range(self) -> None:
        self.mocks[8].return_value = self.locations
        try:
            sanidrive.main()
        except IntentionalLoopBreakException:
            pass

        filtered_appointments = SpyAppointment.captured_appointments
        all_appointments = []
        expected_appointments = []
        for place, date, time, note in zip(PLACES, DATES, TIMES, NOTES):
            all_appointments.append(Appointment(
                place, date, time, note
            ))
        indices = [0, 3, 8, 11, 12, 16]
        for i in indices:
            expected_appointments.append(all_appointments[i])

        msg = '\nfiltered_appointments were:'
        for a in filtered_appointments:
            msg += ('\n\t' + a.__str__())
        print(msg)
        self.assertListEqual(filtered_appointments, expected_appointments, msg)

    def test_tortoli_150_range(self) -> None:
        indices = [0, 1, 3, 4, 10, 11, 12, 13]

if __name__ == '__main__':
    unittest.main()