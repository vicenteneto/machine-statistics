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

from xml.etree import ElementTree

from paramiko import SFTPClient, Transport


def validate_parameters(element, parameters):
    return all(parameter in element.attrib for parameter in parameters)


tree = ElementTree.parse('config.xml')
alert_parameters = ('type', 'limit')
client_parameters = ('ip', 'username', 'password')


class Alert(object):
    def __init__(self, type_, limit):
        self.type = type_
        self.limit = limit

    @staticmethod
    def from_element(element):
        return Alert(element.get('type'), element.get('limit'))


class Client(object):
    client = None

    def __init__(self, ip, port, username, password, mail, alerts):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.mail = mail
        self.alerts = [Alert.from_element(alert_element) for alert_element in alerts if
                       validate_parameters(alert_element, alert_parameters)]

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
        sftp.put('client.py', 'client.py')

    def execute_client_script(self):
        session = self.client.open_channel(kind='session')
        session.exec_command('python client.py')

        while True:
            if session.exit_status_ready():
                break

        session.close()


for client_element in tree.getroot():
    if validate_parameters(client_element, client_parameters):
        client = Client.from_element(client_element)

        client.connect()
        client.send_client_script()
        client.execute_client_script()
        client.close()
