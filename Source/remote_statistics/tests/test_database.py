from unittest import TestCase

from remote_statistics.database import Session, SessionError


class TestSession(TestCase):
    def test_instantiate_from_config_element__invalid_element__session_error(self):
        with self.assertRaises(SessionError):
            self.assertIsNone(Session.from_config_element(None))

    def test_instantiate_from_config_element__invalid_database_name__session_error(self):
        with self.assertRaises(SessionError):
            self.assertIsNone(Session.from_config_element({}))
