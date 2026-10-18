import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from sanidrive import sanidrive

class TestLocationFiltering(unittest.TestCase):
    def setUp(self) -> None:
        patchers = [
            patch('sanidrive.sanidrive.parse_arguments'),
            patch('sanidrive.sanidrive.cls'),
            patch('sanidrive.sanidrive.run'),
            #patch('sanidrive.sanidrive.init_driver'),
            patch('sanidrive.sanidrive.title')
        ]

        self.mocks: list[MagicMock] = []
        for p in patchers:
            self.mocks.append(p.start())

        self.addCleanup(patch.stopall)
        return super().setUp()

    def test_full_traversal_no_backs(self) -> None:
        sanidrive.main()
        self.mocks[1].side_effect = lambda: print('mock cls called')
        def t():
            print('mock parser called')
        self.mocks[0].side_effect = t

        for mock in self.mocks:
            mock.assert_called()

    def test_full_traversal_full_backs(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()