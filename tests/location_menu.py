import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from sanidrive import sanidrive
from sanidrive.location import (LocationPickMenu,
                                LocationPickMenuV2,
                                interactive_location,
                                interactive_location_v2)

class SpyLocationPickMenu(LocationPickMenu):
    captured_context = {}

    def run(self, *args, **kwargs) -> dict:
        ret = super().run(*args, **kwargs)
        SpyLocationPickMenu.captured_context = ret
        return ret

class SpyLocationPickMenuV2(LocationPickMenuV2):
    captured_context = {}
    captured_context_history = {}

    def run(self) -> dict:
        ret = super().run()
        SpyLocationPickMenuV2.captured_context = ret
        SpyLocationPickMenuV2.captured_stack = self.stack
        return ret



class TestLocationMenu(unittest.TestCase):
    def setUp(self) -> None:
        patchers = [
            patch('sanidrive.sanidrive.parse_arguments'),
            patch('sanidrive.sanidrive.cls'),
            patch('sanidrive.sanidrive.run'),
            patch('sanidrive.sanidrive.init_driver'),
            patch('sanidrive.sanidrive.title'),
            patch('sanidrive.sanidrive.download_chromedriver'),     # 5
            patch('sanidrive.sanidrive.choose_prescription'),
            patch('sanidrive.location.LocationPickMenu',
                  new=SpyLocationPickMenu),
            patch('builtins.input'),                                # 8
            patch('sanidrive.location.divider'),
            patch('sanidrive.location.cls'),
            patch('sanidrive.location._center'),
            patch('sanidrive.location.print')                       # 12
        ]

        self.mocks: list[MagicMock] = []
        for p in patchers:
            self.mocks.append(p.start())

        self.addCleanup(patch.stopall)
        return super().setUp()

    def helper_location_config_check(self, location, config, expected_config):
        print(location, '\n', config, '\n\n')
        self.assertDictEqual(config, expected_config)           #type: ignore

    def test_back_out(self) -> None:
        self.mocks[8].side_effect = ['']

        location = interactive_location()
        config = SpyLocationPickMenu.captured_context
        expected_config = {}
        self.helper_location_config_check(location, config, expected_config)

    def test_full_traversal_no_backs(self) -> None:
        self.mocks[8].side_effect = [
            'tortoli', 's', '20', 's', 'bari sardo', ''
            ]
        
        location = interactive_location()
        config = SpyLocationPickMenu.captured_context
        expected_config = {
            'comune': 'Tortolì',
            'distance': 20.0,
            'forced_comuni': ['Bari Sardo']
        }
        self.helper_location_config_check(location, config, expected_config)

        
    def test_full_traversal_full_backs(self) -> None:
        self.mocks[8].side_effect = [
            'tortoli', 'n', 'serramanna', 's', '2000', 'n', '20', 's',
            'tortoli', 'cagliari', ''
        ]

        location = interactive_location()
        config = SpyLocationPickMenu.captured_context
        expected_config = {
            'comune': 'Serramanna',
            'distance': 20.0,
            'forced_comuni': ['Tortolì', 'Cagliari']
        }
        self.helper_location_config_check(location, config, expected_config)


    def test_full_traversal_full_backs_abort(self) -> None:
        self.mocks[8].side_effect = [
            'tortoli', 'n', 'serramanna', 's', '2000', 'n', '', '',
        ]

        location = interactive_location()
        config = SpyLocationPickMenu.captured_context
        expected_config = {}

        self.helper_location_config_check(location, config, expected_config)


    def test_is_location_filtering_accurate(self) -> None:
        # download page with many comuni of known distances
        # spoof sanidrive.driver to use that page somehow
        # check results
        pass


class TestLocationMenuV2(unittest.TestCase):
    def setUp(self) -> None:
        patchers = [
            patch('sanidrive.sanidrive.parse_arguments'),
            patch('sanidrive.sanidrive.cls'),
            patch('sanidrive.sanidrive.run'),
            patch('sanidrive.sanidrive.init_driver'),
            patch('sanidrive.sanidrive.title'),
            patch('sanidrive.sanidrive.download_chromedriver'),     # 5
            patch('sanidrive.sanidrive.choose_prescription'),
            patch('sanidrive.location.LocationPickMenuV2',
                  new=SpyLocationPickMenuV2),
            patch('builtins.input'),                                # 8
            patch('sanidrive.location.divider'),
            patch('sanidrive.location.cls'),
            patch('sanidrive.location._center'),
            patch('sanidrive.location.print')                       # 12
        ]

        self.mocks: list[MagicMock] = []
        for p in patchers:
            self.mocks.append(p.start())

        self.addCleanup(patch.stopall)
        return super().setUp()

    def helper_location_config_check(self, locations, config, expected_config,
                                     stack = []):
        print(stack, '\n')
        for location in locations:
            print(location, '\n', config, '\n\n')
        self.assertDictEqual(config, expected_config)           #type: ignore


    def test_back_out(self) -> None:
        self.mocks[8].side_effect = ['']

        location = interactive_location_v2()
        config = SpyLocationPickMenuV2.captured_context
        expected_config = {}
        self.helper_location_config_check(location, config, expected_config)

    def test_full_traversal_full_backs(self) -> None:
            self.mocks[8].side_effect = ['tortoli', '', 'baunei', '20', '',
                                         '25', 's', 's', '', '30', 's', 's',
                                         'serramanna', '15', 's', 'n'
                                         ]
    
            locations = interactive_location_v2()
            config = SpyLocationPickMenuV2.captured_context
            stack = SpyLocationPickMenuV2.captured_stack
            expected_config = {
                'comuni': ['Baunei', 'Serramanna'],
                'distances': [30.0, 15.0],
                'times_looped': 1
            }
            self.helper_location_config_check(locations, config,
                                              expected_config, stack)

    def test_full_traversal_full_backs_loop_twice(self) -> None:
                self.mocks[8].side_effect = ['tortoli', '', 'baunei', '20', '',
                                             '25', 's', 's', '', '30', 's', 's',
                                             'serramanna', '15', 's', 's',
                                             'cagliari', '35', 's', 'n'
                                             ]
        
                locations = interactive_location_v2()
                config = SpyLocationPickMenuV2.captured_context
                stack = SpyLocationPickMenuV2.captured_stack
                expected_config = {
                    'comuni': ['Baunei', 'Serramanna', 'Cagliari'],
                    'distances': [30.0, 15.0, 35.0],
                    'times_looped': 2
                }
                self.helper_location_config_check(locations, config,
                                                  expected_config, stack)






if __name__ == '__main__':
    unittest.main()