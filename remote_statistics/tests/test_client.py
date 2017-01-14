from unittest import TestCase

from remote_statistics.client import File
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
