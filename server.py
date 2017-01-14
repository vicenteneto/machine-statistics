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
import logging

from remote_statistics import load_configuration
from remote_statistics.database import Session, SessionError
from remote_statistics.models import Client
from remote_statistics.smtp import SMTP, SMTPError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

CLIENT_PARAMETERS = ('ip', 'username', 'password')
CONFIG_FILE = 'config.xml'

database, smtp, clients = load_configuration(CONFIG_FILE)

sql_session = None
try:
    sql_session = Session.from_config_element(database)
except SessionError as error:
    pass

smtp_server = None
try:
    smtp_server = SMTP.from_config_element(smtp)
except SMTPError as error:
    pass

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
            metric = client.save_client_data(sql_session, client_data)
            client.send_metric_notifications(metric, smtp_server)

            client.close()
