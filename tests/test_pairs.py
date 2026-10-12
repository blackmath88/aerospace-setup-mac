import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    'pairs', Path(__file__).parents[1] / 'templates' / 'pairs.py'
)
PAIRS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PAIRS)


def monitor(name, screen_id, width, height):
    return {
        'monitor-id': screen_id,
        'screen-id': screen_id,
        'monitor-name': name,
        'is-main': 'built-in' in name.lower(),
        'width': width,
        'height': height,
    }


class WorkspaceTests(unittest.TestCase):
    def test_workspace_groups_repeat_every_five(self):
        self.assertEqual(PAIRS.workspace_group('1'), 1)
        self.assertEqual(PAIRS.workspace_group('6'), 1)
        self.assertEqual(PAIRS.workspace_group('11'), 1)
        self.assertEqual(PAIRS.workspace_group('14'), 4)
        self.assertIsNone(PAIRS.workspace_group('5'))
        self.assertIsNone(PAIRS.workspace_group('not-a-workspace'))

    def test_workspace_for_monitor_slot(self):
        self.assertEqual(PAIRS.workspace_for(3, 0), 3)
        self.assertEqual(PAIRS.workspace_for(3, 1), 8)
        self.assertEqual(PAIRS.workspace_for(3, 2), 13)


class MonitorOrderingTests(unittest.TestCase):
    def test_work_setup_uses_landscape_portrait_builtin_order(self):
        monitors = [
            monitor('Built-in Retina Display', 1, 1512, 982),
            monitor('P24h-30 (2)', 2, 1440, 2560),
            monitor('P24h-30 (1)', 3, 2560, 1440),
        ]
        ordered = PAIRS.ordered_monitors(monitors)
        self.assertEqual(
            [item['monitor-name'] for item in ordered],
            ['P24h-30 (1)', 'P24h-30 (2)', 'Built-in Retina Display'],
        )

    def test_order_does_not_depend_on_aerospace_monitor_id(self):
        monitors = [
            monitor('Built-in Retina Display', 40, 1512, 982),
            monitor('Portrait', 1, 1200, 1920),
            monitor('Landscape', 99, 2560, 1440),
        ]
        ordered = PAIRS.ordered_monitors(monitors)
        self.assertEqual(
            [PAIRS.monitor_role(item) for item in ordered],
            ['landscape', 'portrait', 'built-in'],
        )


if __name__ == '__main__':
    unittest.main()
