import logging
import smtplib
import socket
from email.mime.text import MIMEText


class SMTPError(Exception):
    pass


class SMTP(object):
    def __init__(self, host='', port=0, user=None, password=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        try:
            self.user = user
            self.server = smtplib.SMTP_SSL(host, port, timeout=timeout)

            if user and password:
                self.server.login(user, password)

            logging.info('SMTP server configured with success!')
        except socket.gaierror as error:
            logging.error('%s (%s).', error, host if port is None else '%s:%s' % (host, port))
            raise SMTPError()
        except socket.error as error:
            logging.error('%s (%s:%s).', error, host, port)
            raise SMTPError()
        except (smtplib.SMTPConnectError, smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected) as error:
            logging.error(error)
            raise SMTPError()

    def send_email(self, subject, to, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = to

            self.server.sendmail(self.user, [to], msg.as_string())
        except (smtplib.SMTPHeloError, smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused,
                smtplib.SMTPDataError) as error:
            logging.error(error)

    @staticmethod
    def from_config_element(smtp_config):
        if smtp_config is None:
            logging.warning('SMTP configuration element does not found!')
            return None

        logging.info('SMTP configuration element found!')

        host = smtp_config.get('host')
        port = smtp_config.get('port')
        user = smtp_config.get('user')
        password = smtp_config.get('password')

        return SMTP(host, port, user, password)
