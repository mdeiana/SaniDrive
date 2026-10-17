import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sanidrive.util import InteractiveMenu
from sanidrive.location import Location

class TestInteractiveMenu(unittest.TestCase):
    """Tests for the reusable context-driven menu state machine."""

    def test_advances_through_steps_and_preserves_context(self):
        """A normal happy path should advance through the workflow and carry context."""

        def start(context):
            context["comune"] = "Cagliari"
            return "ADVANCE", ""

        def confirm(context):
            self.assertEqual(context["comune"], "Cagliari")
            context["confirmed"] = True
            return "ADVANCE", ""

        workflow = {
            "start": {"handler": start, "next": "confirm"},
            "confirm": {"handler": confirm, "next": None},
        }

        menu = InteractiveMenu(workflow, "start", "")
        menu.print_header = lambda: None
        menu.print_context = lambda: None
        menu.print_warning = lambda: None

        result = menu.run()

        self.assertEqual(
            result,
            {"comune": "Cagliari", "confirmed": True},
        )

    def test_back_from_transient_step_returns_to_previous_non_transient_step(self):
        """A BACK should unwind only the transient step and resume the previous state."""

        def start(context):
            if context.get("reentered"):
                context["done"] = True
                return "END", ""
            context["reentered"] = True
            return "ADVANCE", ""

        def confirm(context):
            return "BACK", ""

        workflow = {
            "start": {"handler": start, "next": "confirm"},
            "confirm": {"handler": confirm, "next": None, "transient": True},
        }

        menu = InteractiveMenu(workflow, "start", "")
        menu.print_header = lambda: None
        menu.print_context = lambda: None
        menu.print_warning = lambda: None

        result = menu.run()

        self.assertEqual(
            result,
            {"reentered": True, "done": True},
        )

    def test_back_from_first_step_should_not_crash(self):
        """This test exposes the actual bug in the current BACK implementation."""

        def start(context):
            context["cancelled"] = True
            return "BACK", ""

        workflow = {"start": {"handler": start, "next": "confirm"}}

        menu = InteractiveMenu(workflow, "start", "")
        menu.print_header = lambda: None
        menu.print_context = lambda: None
        menu.print_warning = lambda: None

        #with self.assertRaises(IndexError):
        #    menu.run()

        result = menu.run()
        self.assertEqual(result, None)

class TempManualTest(unittest.TestCase):
    def test_manual(self):
        loc = Location('Tortolì', 0, [])

        self.assertTrue(loc.can_reach('Tortolì'))
        self.assertEqual(loc.get_distance_to('Tortolì'), 0)


if __name__ == "__main__":
    unittest.main()
