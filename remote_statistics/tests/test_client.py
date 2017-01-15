from datetime import datetime
from unittest import TestCase

from remote_statistics.client import File, MachineStatistics
from remote_statistics.tests import util


class TestClientFile(TestCase):
    def test_instantiate_file__wrong_filename__value_error(self):
        with self.assertRaises(ValueError):
            File(util.ENCRYPTED_FILE_NAME)

    def test_instantiate_file__correct_filename__file_object(self):
        util.create_plaintext_file()

        with File(util.DECRYPTED_FILE_NAME) as file_:
            self.assertEqual(file_.file.name, util.DECRYPTED_FILE_NAME)

        util.delete_file(util.DECRYPTED_FILE_NAME)

    def test_decrypt_file(self):
        util.create_plaintext_file()

        with File(util.DECRYPTED_FILE_NAME) as file_:
            file_.encrypt()

        with open(util.ENCRYPTED_FILE_NAME) as file_:
            self.assertNotEqual(file_.read(), util.FILE_TEXT)

        util.delete_file(util.ENCRYPTED_FILE_NAME)
        util.delete_file(util.DECRYPTED_FILE_NAME)


class TestMachineStatistics(TestCase):
    def test_get_execution_date(self):
        before_execution_time = datetime.utcnow()
        machine_statistics = MachineStatistics()
        after_execution_time = datetime.utcnow()

        self.assertGreater(machine_statistics.execution_date, before_execution_time)
        self.assertLess(machine_statistics.execution_date, after_execution_time)

    def test_collect_cpu_usage(self):
        machine_statistics = MachineStatistics()

        self.assertIsNone(machine_statistics.cpu_percent)

        machine_statistics.collect_cpu_usage()

        self.assertIsNotNone(machine_statistics.cpu_percent)
        self.assertIsInstance(machine_statistics.cpu_percent, float)

    def test_collect_memory_usage(self):
        machine_statistics = MachineStatistics()

        self.assertIsNone(machine_statistics.memory_used)
        self.assertIsNone(machine_statistics.memory_percent)

        machine_statistics.collect_memory_usage()

        self.assertIsNotNone(machine_statistics.memory_used)
        self.assertIsNotNone(machine_statistics.memory_percent)
        self.assertIsInstance(machine_statistics.memory_used, int)
        self.assertIsInstance(machine_statistics.memory_percent, float)

    def test_collect_uptime(self):
        machine_statistics = MachineStatistics()

        self.assertIsNone(machine_statistics.uptime)

        machine_statistics.collect_uptime()

        self.assertIsNotNone(machine_statistics.uptime)
        self.assertIsInstance(machine_statistics.uptime, float)

    def test_collect_disks_usage(self):
        machine_statistics = MachineStatistics()

        self.assertFalse(machine_statistics.disk_partitions)

        machine_statistics.collect_disks_usage()

        self.assertTrue(machine_statistics.disk_partitions)
        self.assertIn('mountpoint', machine_statistics.disk_partitions[0])
        self.assertIn('used', machine_statistics.disk_partitions[0])
        self.assertIn('percent', machine_statistics.disk_partitions[0])
        self.assertIsInstance(machine_statistics.disk_partitions[0]['mountpoint'], str)
        self.assertIsInstance(machine_statistics.disk_partitions[0]['used'], int)
        self.assertIsInstance(machine_statistics.disk_partitions[0]['percent'], float)
