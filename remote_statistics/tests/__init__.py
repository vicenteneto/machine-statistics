import errno
from unittest import TestCase

from remote_statistics import load_configuration


class TestRemoteStatistics(TestCase):
    def test_load_configuration__non_existent_configuration__sys_exit(self):
        with self.assertRaises(SystemExit) as cm:
            load_configuration('non_existent_configuration.xml')

        self.assertEqual(cm.exception.code, errno.ENOENT)

    def test_load_configuration__invalid_configuration__sys_exit(self):
        with self.assertRaises(SystemExit) as cm:
            load_configuration('remote_statistics/tests/invalid_config.xml')

        self.assertEqual(cm.exception.code, errno.EBFONT)

    def test_load_configuration__valid_configuration__configuration_tuple(self):
        database, smtp, clients = load_configuration('config.xml')

        self.assertIsNotNone(database)
        self.assertIsNotNone(smtp)
        self.assertIsNotNone(clients)
