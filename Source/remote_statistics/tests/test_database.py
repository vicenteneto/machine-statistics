from unittest import TestCase

from remote_statistics.database import Session


class TestSession(TestCase):
    def test_instantiate_from_config_element__invalid_element__none(self):
        self.assertIsNone(Session.from_config_element(None))

    def test_instantiate_from_config_element__invalid_database_name__none(self):
        self.assertIsNone(Session.from_config_element({}))
