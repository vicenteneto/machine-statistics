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
import pickle
from xml.etree import ElementTree

from Crypto.Cipher import AES
from paramiko import SFTPClient, Transport
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from sqlalchemy.types import DateTime, Integer, String

ALERT_PARAMETERS = ('type', 'limit')
CLIENT_PARAMETERS = ('ip', 'username', 'password')
CONFIG_FILE = 'config/config.xml'

engine = create_engine('mysql://root:6esncj4m@localhost/metrics')
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


class Metric(Base):
    __tablename__ = 'metrics'

    id = Column(Integer, primary_key=True)
    execution_date = Column(DateTime, nullable=False)


class Client(Base):
    __tablename__ = 'clients'

    client = None

    id = Column(Integer, primary_key=True)
    ip = Column(String(15), unique=True)

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

    def connect(self):
        self.client = Transport((self.ip, self.port))
        self.client.connect(username=self.username, password=self.password)

    def close(self):
        self.client.close()

    def send_client_script(self):
        sftp = SFTPClient.from_transport(self.client)
        sftp.put('client.py', '/tmp/client.py')
        sftp.put('client-requirements.txt', '/tmp/requirements.txt')

    def execute_client_script(self):
        session = self.client.open_channel(kind='session')

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

    def create_client_data_file_name(self):
        return 'client_data_%s.json' % self.ip

    def save_client_data(self):
        client_data_filename = self.create_client_data_file_name()
        sftp = SFTPClient.from_transport(self.client)
        sftp.get('/tmp/client_data.json.enc', '/tmp/' + client_data_filename + '.enc')

    def decrypt_client_data(self):
        client_data_filename = self.create_client_data_file_name()
        with File('/tmp/' + client_data_filename + '.enc') as data_file:
            data_file.decrypt()

    def print_metrics(self):
        client_data_filename = self.create_client_data_file_name()
        with open('/tmp/' + client_data_filename) as data_file:
            print pickle.load(data_file)


Base.metadata.create_all(engine)
tree = ElementTree.parse(CONFIG_FILE)

for client_element in tree.getroot():
    if all(parameter in client_element.attrib for parameter in CLIENT_PARAMETERS):
        client = Client.from_element(client_element)

        client.connect()
        client.send_client_script()
        client.execute_client_script()
        client.save_client_data()
        client.decrypt_client_data()
        client.print_metrics()
        client.close()
