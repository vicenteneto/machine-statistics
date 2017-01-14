from unittest import TestCase

from mock import patch

from remote_statistics.smtp import SMTP, SMTPError


class TestSMTP(TestCase):
    def test_instantiate_smtp__wrong_host__smtp_error(self):
        with self.assertRaises(SMTPError):
            SMTP(host='smtp.google.coma', timeout=1)

    def test_instantiate_smtp__wrong_port__smtp_error(self):
        with self.assertRaises(SMTPError):
            SMTP(host='smtp.google.com', port=80, timeout=1)

    def test_instantiate_smtp__wrong_user_and_password__smtp_error(self):
        with self.assertRaises(SMTPError):
            SMTP(host='smtp.google.com', port=465, user='user', password='password', timeout=1)

    def test_instantiate_smtp(self):
        with patch('smtplib.SMTP_SSL'):
            SMTP(host='smtp.google.com', port=465, user='valid-user', password='correct-password')

    def test_instantiate_from_config_element(self):
        self.assertIsNone(SMTP.from_config_element(None))

    def test_send_email(self):
        with patch('smtplib.SMTP_SSL'):
            smtp = SMTP(host='smtp.google.com', port=465, user='valid-user', password='correct-password')
            smtp.send_email('subject', 'to', 'message')
