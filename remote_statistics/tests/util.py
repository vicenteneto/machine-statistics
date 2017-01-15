import os
from xml.etree import ElementTree

from remote_statistics.client import File

DECRYPTED_FILE_NAME = 'testfile.txt'
ENCRYPTED_FILE_NAME = 'testfile.txt.enc'
FILE_TEXT = 'Text to be encrypted'


def delete_file(filename):
    assert os.path.exists(filename)
    os.remove(filename)
    assert not os.path.exists(filename)


def create_plaintext_file(filename=DECRYPTED_FILE_NAME):
    assert not os.path.exists(filename)
    with open(filename, 'wb') as file_:
        file_.write(FILE_TEXT)
    assert os.path.exists(filename)


def create_ciphertext_file(filename=DECRYPTED_FILE_NAME):
    create_plaintext_file(filename)

    with File(filename) as file_:
        file_.encrypt()

    delete_file(filename)


def create_config_element():
    root = ElementTree.Element('config')
    ElementTree.SubElement(root, 'database')
    ElementTree.SubElement(root, 'smtp')
    ElementTree.SubElement(root, 'clients')

    return root


def create_client_element():
    client = '''
    <client ip="192.168.25.7" port="22" username="vicente" password="password" mail="email@gmail.com">
        <alert type="memory" limit="50%"/>
        <alert type="cpu" limit="20%"/>
        <alert type="uptime" limit="10"/>
    </client>
    '''
    return ElementTree.fromstring(client)
