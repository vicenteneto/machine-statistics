import pickle

import paramiko
from paramiko import SFTPClient
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import BigInteger, DateTime, Float, Integer, String

from remote_statistics.crypt import File

Base = declarative_base()

ALERT_PARAMETERS = ('type', 'limit')


class Alert(object):
    def __init__(self, type_, limit):
        self.type = type_
        self.limit = limit
        self.use_percentage = False

    def is_valid_limit(self):
        if self.limit.endswith('%'):
            self.use_percentage = True
            self.limit = self.limit[:-1]

        try:
            self.limit = float(self.limit)
            return True
        except ValueError:
            return False

    @staticmethod
    def from_element(element):
        return Alert(element.get('type'), element.get('limit'))


class DiskMetric(Base):
    __tablename__ = 'disk_metric'

    disk_metric_id = Column(Integer, primary_key=True)
    metric_id = Column(Integer, ForeignKey('metric.metric_id'))
    mountpoint = Column(String(50), nullable=False)
    used = Column(BigInteger, nullable=False)
    percent = Column(Float, nullable=False)


class Metric(Base):
    __tablename__ = 'metric'

    metric_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client.client_id'))
    execution_date = Column(DateTime, nullable=False)
    cpu_percent = Column(Float, nullable=False)
    memory_used = Column(BigInteger, nullable=False)
    memory_percent = Column(Float, nullable=False)
    uptime = Column(BigInteger, nullable=False)
    disks = relationship(DiskMetric, primaryjoin=metric_id.__eq__(DiskMetric.metric_id))

    def analyze_cpu_percent(self, value):
        return self.cpu_percent > value

    def analyze_memory(self, value):
        return self.memory_used > value

    def analyze_memory_percent(self, value):
        return self.memory_percent > value

    def analyze_uptime(self, time):
        return self.uptime > time

    def analyze_disks(self, value):
        return bool([disk for disk in self.disks if disk.used > value])

    def analyze_disks_percent(self, value):
        return bool([disk for disk in self.disks if disk.percent > value])

    def create_mail_message(self, client, alert):
        attributes = {
            'cpu': self.cpu_percent,
            'memory': {
                'used': self.memory_used,
                'percentage': self.memory_percent,
            },
            'uptime': self.uptime
        }

        base_message = 'Host %s on alert:\n'
        if alert.type in attributes:
            attribute = attributes[alert.type]

            if isinstance(attribute, dict):
                attribute = attribute['percentage'] if alert.use_percentage else attribute['used']

            return (base_message + 'Maximum desired %s usage: %s\nCurrent %s usage: %s') % \
                   (client.ip, alert.type, alert.limit, alert.type, attribute)
        else:
            return base_message


class Client(Base):
    __tablename__ = 'client'

    transport = None

    client_id = Column(Integer, primary_key=True)
    ip = Column(String(15), nullable=False, unique=True)
    metrics = relationship(Metric, primaryjoin=client_id.__eq__(Metric.client_id))

    def __init__(self, ip, port, username, password, mail, alerts):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.mail = mail
        self.alerts = [Alert.from_element(alert_element) for alert_element in alerts if
                       all(parameter in alert_element.attrib for parameter in ALERT_PARAMETERS)]

    @staticmethod
    def from_element(element):
        return Client(element.get('ip'), int(element.get('port', 22)), element.get('username'),
                      element.get('password'),
                      element.get('mail', None), list(element))

    def __create_client_data_file_name(self):
        return 'client_data_%s.json' % self.ip

    def load_or_create(self, session):
        client_db = session.query(Client).filter_by(ip=self.ip).first()

        if not client_db:
            session.add(self)
            session.commit()
        else:
            self.client_id = client_db.client_id
            self.metrics = client_db.metrics

    def connect(self):
        self.transport = Transport((self.ip, self.port))
        self.transport.connect(username=self.username, password=self.password)

    def send_client_script(self):
        sftp = SFTPClient.from_transport(self.transport)
        sftp.put('remote_statistics/client.py', '/tmp/client.py')
        sftp.put('requirements/client-requirements.txt', '/tmp/requirements.txt')

    def execute_client_script(self):
        session = self.transport.open_multi_commands_channel(kind='session')
        session.add_command('cd /tmp')
        session.add_command('virtualenv --python=/usr/local/lib/python2.7.13/bin/python pyEnv')
        session.add_command('source pyEnv/bin/activate')
        session.add_command('pip install -r requirements.txt')
        session.add_command('python client.py')
        session.exec_commands()

        while True:
            if session.exit_status_ready():
                break

        session.close()

    def get_client_data(self):
        client_data_filename = self.__create_client_data_file_name()
        sftp = SFTPClient.from_transport(self.transport)
        sftp.get('/tmp/client_data.json.enc', '/tmp/' + client_data_filename + '.enc')

    def decrypt_client_data(self):
        client_data_filename = self.__create_client_data_file_name()
        with File('/tmp/' + client_data_filename + '.enc') as data_file:
            data_file.decrypt()

    def load_client_data(self):
        client_data_filename = self.__create_client_data_file_name()
        with open('/tmp/' + client_data_filename) as data_file:
            return pickle.load(data_file)

    def save_client_data(self, session, client_data):
        disks = [DiskMetric(**partition) for partition in client_data.pop('disk_partitions')]
        metric = Metric(**client_data)
        metric.disks = disks

        self.metrics.append(metric)

        instances = list()
        if not self.client_id:
            instances.append(self)
        else:
            metric.client_id = self.client_id
        instances.append(metric)
        instances.extend(disks)

        if session:
            session.add_all(instances)
            session.commit()

        return metric

    def send_metric_notifications(self, metric, smtp_server):
        validate_alert_functions = {
            'cpu': {
                'percentage': metric.analyze_cpu_percent
            },
            'memory': {
                'used': metric.analyze_memory,
                'percentage': metric.analyze_memory_percent,
            },
            'uptime': metric.analyze_uptime,
            'disk': {
                'used': metric.analyze_disks,
                'percentage': metric.analyze_disks_percent
            }
        }

        for alert in self.alerts:
            if alert.is_valid_limit() and alert.type in validate_alert_functions:
                validate_func = validate_alert_functions[alert.type]

                if isinstance(validate_func, dict):
                    validate_func = validate_func['percentage'] if alert.use_percentage else validate_func['used']

                if validate_func(alert.limit):
                    message = metric.create_mail_message(self, alert)
                    smtp_server.send_email('Remote machine on alert!', self.mail, message)

    def close(self):
        self.transport.close()


class Channel(object):
    def __init__(self, session):
        self.session = session
        self.command = None

    def add_command(self, command):
        self.command = command if not self.command else self.command + ' && ' + command

    def exec_commands(self):
        if self.command:
            self.session.exec_command(self.command)

    def exit_status_ready(self):
        return self.session.exit_status_ready()

    def close(self):
        self.session.close()


class Transport(paramiko.Transport):
    def open_multi_commands_channel(self, kind, dest_addr=None, src_addr=None, window_size=None,
                                    max_packet_size=None,
                                    timeout=None):
        session = super(Transport, self).open_channel(kind, dest_addr, src_addr, window_size, max_packet_size,
                                                      timeout)
        return Channel(session)
