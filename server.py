"""
1. Installed on a single central machine in the same intranet.
2. Each client is configured in a server config xml file something like this
    <client ip="127.0.0.1" port="22" username="user" password="password" mail="asa@email.com">
        <alert type="memory" limit="50%"/>
        <alert type="cpu" limit="20%"/>
    </client>
3. When executed, the server script should connect to each client using ssh, upload the client script in a temp
directory, execute it and get the response.
4. After receiving the response from the client script, server script should decode it and stores it into a relational
database along with client ip. This collected data is consumed by another application, that is out of scope, but you may
design the database table yourself.
5. The server based upon the "alert" configuration of each client sends a mail notification. The notification is sent to
the client configured email address using SMTP. Use a simple text mail format with some detail about the alert. event
logs must be sent via email every time without any condition.
"""
import errno
import logging
import pickle
import smtplib
import socket
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

from Crypto.Cipher import AES
from paramiko import SFTPClient, Transport
from sqlalchemy.engine import create_engine, url
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import BigInteger, DateTime, Float, Integer, String

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ALERT_PARAMETERS = ('type', 'limit')
CLIENT_PARAMETERS = ('ip', 'username', 'password')
CONFIG_FILE = 'config.xml'

Base = declarative_base()


class File(object):
    KEY = b'\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18'

    def __init__(self, filename):
        if not filename.endswith('.enc'):
            raise ValueError('Filename must ends with ".enc"')
        self.file = open(filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def __decrypt_text(self, cipher_text):
        iv = cipher_text[:AES.block_size]
        cipher = AES.new(self.KEY, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(cipher_text[AES.block_size:])
        return plaintext.rstrip(b'\0')

    def decrypt(self):
        cipher_text = self.file.read()
        plaintext = self.__decrypt_text(cipher_text)
        with open(self.file.name[:-4], 'wb') as txt_file:
            txt_file.write(plaintext)


class Alert(object):
    def __init__(self, type_, limit):
        self.type = type_
        self.limit = limit

    @staticmethod
    def from_element(element):
        return Alert(element.get('type'), element.get('limit'))


class BatchCommands(object):
    def __init__(self, session, command):
        self.session = session
        self.command = command

    def add_command(self, command):
        self.command += ' && ' + command

    def exec_commands(self):
        self.session.exec_command(self.command)


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
    uptime = Column(DateTime, nullable=False)
    disks = relationship(DiskMetric, primaryjoin=metric_id.__eq__(DiskMetric.metric_id))


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
        return Client(element.get('ip'), int(element.get('port', 22)), element.get('username'), element.get('password'),
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

    def connect(self):
        self.transport = Transport((self.ip, self.port))
        self.transport.connect(username=self.username, password=self.password)

    def send_client_script(self):
        sftp = SFTPClient.from_transport(self.transport)
        sftp.put('client.py', '/tmp/client.py')
        sftp.put('client-requirements.txt', '/tmp/requirements.txt')

    def execute_client_script(self):
        session = self.transport.open_channel(kind='session')

        batch = BatchCommands(session, 'cd /tmp')
        batch.add_command('virtualenv --python=/usr/local/lib/python2.7.13/bin/python pyEnv')
        batch.add_command('source pyEnv/bin/activate')
        batch.add_command('pip install -r requirements.txt')
        batch.add_command('python client.py')
        batch.exec_commands()

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
        session.add_all(instances)
        session.commit()

    def close(self):
        self.transport.close()


def get_config_root():
    try:
        tree = ElementTree.parse(CONFIG_FILE)
        logging.info('Configuration file loaded with success!')
        return tree.getroot()
    except IOError as error:
        logging.error('%s. Terminating program.', error)
        sys.exit(errno.ENOENT)
    except ParseError as error:
        logging.error('%s. Terminating program', error)
        sys.exit()


def create_mysql_session(database_config):
    if database_config is None:
        logging.warning('MySQL configuration element does not found on %s', CONFIG_FILE)
        return None

    logging.info('MySQL configuration element found on %s', CONFIG_FILE)

    host = database_config.get('host')
    port = database_config.get('port')
    username = database_config.get('username')
    password = database_config.get('password')
    database_name = database_config.get('database')

    if not database_name:
        logging.info('Database name does not found on MySQL configuration')
        return None

    engine = create_engine(url.URL('mysql', username, password, host, port, database_name))

    session = None
    try:
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        logging.info('MySQL session configured with success!')
    except OperationalError as error:
        logging.error('%s', error)

    return session


def connect_to_smtp_server(smtp_config):
    if smtp_config is None:
        logging.warning('SMTP configuration element does not found on %s', CONFIG_FILE)
        return None

    logging.info('SMTP configuration element found on %s', CONFIG_FILE)

    server = None
    host = smtp_config.get('host')
    port = smtp_config.get('port')
    user = smtp_config.get('user')
    password = smtp_config.get('password')

    try:
        server = smtplib.SMTP_SSL(host, port)
        server.login(user, password)
        logging.info('SMTP server configured with success!')
    except socket.gaierror as error:
        logging.error('%s (%s).', error, host if port is None else '%s:%s' % (host, port))
    except socket.error as error:
        logging.error('%s (%s:%s).', error, host, port)
    except (smtplib.SMTPConnectError, smtplib.SMTPAuthenticationError) as error:
        logging.error(error)
        server = None

    return server


def send_email(to, message):
    try:
        # smtp_server.sendmail(from_, [to], message)
        pass
    except:
        pass


config_root = get_config_root()
database = config_root.find('database')
smtp = config_root.find('smtp')
clients = config_root.find('clients')

sql_session = create_mysql_session(database)
smtp_server = connect_to_smtp_server(smtp)

if clients is not None:
    for client_element in list(clients):
        if all(parameter in client_element.attrib for parameter in CLIENT_PARAMETERS):
            client = Client.from_element(client_element)

            client.load_or_create(sql_session)
            client.connect()
            client.send_client_script()
            client.execute_client_script()
            client.get_client_data()
            client.decrypt_client_data()
            client_data = client.load_client_data()
            client.save_client_data(sql_session, client_data)

            client.close()
